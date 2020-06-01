# Ignore FutureWarning from H5py<=2.7.1
import warnings
warnings.filterwarnings('ignore', category=FutureWarning)

import os
import re
import time
import json
import glob
import sys
import gc
import logging
import lib_edge.oodida as o


'''
Globals variables:
* CAR_NUMBER
* LOG_FILE

See bottom for declaration.
'''

def main(assignment_function):
    input_path = './state/edge_out/assignment_car_' + CAR_NUMBER + '_id_*.json'
    output_path_without_id = './state/edge_in/edge_result_car_' + CAR_NUMBER + '_id_{}.json'

    logging.basicConfig(filename=LOG_FILE,level=logging.DEBUG)
    msg = ' {} in car{} - {}.'

    # Create a dictionary of assignment states
    assignment_states = dict()

    print('Start listening.')
    while True:
        # list all assignments
        input_files = glob.glob(input_path)
        # loop over availiable assignments
        for ass_file in input_files:
            try:
                print('Found new assignment.')
                json_dict = o.JSONtoConfig(ass_file)

                # Send state to the assignment_function
                id_number = get_id_from_json_assignment(ass_file)
                result = assignment_function(json_dict, assignment_states, id_number)

                if result != None:
                    output_path = output_path_without_id.format(id_number)
                    output_path_tmp = output_path + '_tmp_'

                    writeConfigToJSON(result, output_path_tmp)
                    os.rename(output_path_tmp, output_path)

                os.remove(ass_file)
                gc.collect() # Improves the memory a bit more

            except OSError as exc:
                # probably a race condition
                logging.exception(msg.format('OSError', CAR_NUMBER, os.strerror(exc.errno)))
                filesize = os.stat(ass_file).st_size
                logging.debug(' {} ({} bytes)'.format(ass_file, filesize))
            except ValueError as e:
                logging.exception(msg.format('ValueError', CAR_NUMBER, e))
                filesize = os.stat(ass_file).st_size
                logging.debug(' {} ({} bytes)'.format(ass_file, filesize))
            except:
                logging.exception(msg.format('Unexpected Error', CAR_NUMBER, sys.exc_info()[0]))
                raise
        time.sleep(0.5)


def perform_assignment(json_dict, assignment_states, id_number):
    '''
    Perform one of the predefined assignments
    '''

    mode = json_dict['type']
    assert mode in ['PingPong','FedAvg', 'COOP', 'FSVRG', 'init_ann', 'destroy_ann', 'init_svrg_ann']

    if mode == 'PingPong':
        result = ass.pong()
        result_json = dict()
        result_json['result'] = result
        return result_json

    elif mode == 'init_ann':
        # init the model objects
        decay = json_dict['decay']
        lr = json_dict['lr']
        E = json_dict['E']
        B = json_dict['B']
        dataset = json_dict['dataset']

        if dataset == 'MNIST':
            image_path = ['data/mnist/car' + CAR_NUMBER + '-images.byte']
            label_path = ['data/mnist/car' + CAR_NUMBER + '-labels.byte']
            model = ass.Mnist_Model(lr, decay, E, B, image_path, label_path)
        elif dataset == 'MNIST-non-iid':
            image_path = ['data/mnist-non-iid/car' + CAR_NUMBER + '-images.byte']
            label_path = ['data/mnist-non-iid/car' + CAR_NUMBER + '-labels.byte']
            model = ass.Mnist_Model(lr, decay, E, B, image_path, label_path)
        elif dataset.startswith('MNIST_noniid_cv') or dataset.startswith('MNIST_iid_cv'):
            match = re.search(r'(?<=_cv)\d+', dataset)
            val_fold = int(match.group(0))
            folds = list(range(1, 6))
            folds.remove(val_fold)

            if dataset.startswith('MNIST_noniid_cv'):
                image_path = 'data/mnist_noniid_cv/fold{}/car' + CAR_NUMBER + '-images.byte'
                label_path = 'data/mnist_noniid_cv/fold{}/car' + CAR_NUMBER + '-labels.byte'
            else:
                image_path = 'data/mnist_iid_cv/fold{}/car' + CAR_NUMBER + '-images.byte'
                label_path = 'data/mnist_iid_cv/fold{}/car' + CAR_NUMBER + '-labels.byte'

            image_paths = [image_path.format(num) for num in folds]
            label_paths = [label_path.format(num) for num in folds]
            model = ass.Mnist_Model(lr, decay, E, B, image_paths, label_paths)
        else:
            sys.exit('Missing dataset')
        assignment_states[id_number] = model

        return None

    elif mode == 'init_svrg_ann':
        # init a model specific to FSVRG
        step_size_k = json_dict['step_size']
        dataset = json_dict['dataset']

        if dataset == 'MNIST':
            image_path = ['data/mnist/car' + CAR_NUMBER + '-images.byte']
            label_path = ['data/mnist/car' + CAR_NUMBER + '-labels.byte']
            model = ass.Fsvrg_Mnist_Model(step_size_k, image_path, label_path)
        elif dataset == 'MNIST-non-iid':
            image_path = ['data/mnist-non-iid/car' + CAR_NUMBER + '-images.byte']
            label_path = ['data/mnist-non-iid/car' + CAR_NUMBER + '-labels.byte']
            model = ass.Fsvrg_Mnist_Model(step_size_k, image_path, label_path)
        elif dataset.startswith('MNIST_noniid_cv') or dataset.startswith('MNIST_iid_cv'):
            match = re.search(r'(?<=_cv)\d+', dataset)
            val_fold = int(match.group(0))
            folds = list(range(1, 6))
            folds.remove(val_fold)

            if dataset.startswith('MNIST_noniid_cv'):
                image_path = 'data/mnist_noniid_cv/fold{}/car' + CAR_NUMBER + '-images.byte'
                label_path = 'data/mnist_noniid_cv/fold{}/car' + CAR_NUMBER + '-labels.byte'
            else:
                image_path = 'data/mnist_iid_cv/fold{}/car' + CAR_NUMBER + '-images.byte'
                label_path = 'data/mnist_iid_cv/fold{}/car' + CAR_NUMBER + '-labels.byte'
            image_paths = [image_path.format(num) for num in folds]
            label_paths = [label_path.format(num) for num in folds]
            model = ass.Fsvrg_Mnist_Model(step_size_k, image_paths, label_paths)
        else:
            sys.exit('Missing dataset')
        assignment_states[id_number] = model

    elif mode == 'destroy_ann':
        # Remove model objects from state
        model = assignment_states[id_number]
        model.on_destroy()
        assignment_states[id_number] = None
        del assignment_states[id_number]

        return None

    else: # Train the ANN model. The procedure is the same for FedAvg and COOP, but FSVRG needs special treatment.
        model = assignment_states[id_number]
        model_params = json_dict['model']
        w_list = model_params['w']
        b_list = model_params['b']

        if mode == 'FSVRG':
            global_gradients_w = json_dict['gradients_w']
            global_gradients_b = json_dict['gradients_b']
            ws, bs = model.train(w_list, b_list, global_gradients_w,
                                 global_gradients_b)
        else :
            ws, bs = model.train(w_list, b_list)

        params = dict()
        params['w'] = ws
        params['b'] = bs
        params['n_k'] = len(model.data[1]) # only really used by FedAvg at the moment
        result_json = dict()
        result_json['result'] = params

        return result_json


def get_id_from_json_assignment(input_file_name):
    '''
    Matches and returns the integer preceded by "_id_"
    '''
    match = re.search(r'(?<=_id_)\d+', input_file_name)
    id_number = int(match.group(0))
    return id_number


def writeConfigToJSON(config, path_name):

    # does file name exist?
    while os.path.exists(path_name):
        print("Unprocessed file remaining. Waiting...")
        time.sleep(5)

    # file does not exist:
    with open(path_name, 'w') as fp:
        json.dump(config, fp)

    print("File ", path_name, " written.")


CAR_NUMBER = sys.argv[1] if len(sys.argv) > 1 else '1'
LOG_FILE = sys.argv[2] if len(sys.argv) > 2 else './logs/car_{}.log'.format(CAR_NUMBER)

if __name__ == '__main__':
    import lib.utils as ut
    import lib_edge.assignment as ass

    main(perform_assignment)
