-module(server).
-export([
  cloud/1,
  assignment_handler/3,
  exit_simulation/0,
  print_connections/0
]).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Central server
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% The cloud process relays information to the user; with each new
% assignment, an assignment_handler is spawned that takes care of
% sending information to cars and performs off-board analytics tasks
cloud(Cars) ->
% Cars is a list of {Pid, Name}
  io:format("~p cars connected.~n", [length(Cars)]),

  receive

  % a new car joined the network
  {new_car, Pid, Name} ->
    % add Pid of new car only if not in Car_Pids
    Names = lists:map(fun({_, X}) -> X end, Cars),
    io:format("Car~p just connected with pid: ~p~n", [Name, Pid]),
    case lists:member(Name, Names) of
      true  -> cloud(Cars);
      false -> cloud([{Pid, Name} | Cars])
    end;

  % assignment from user
  {assignment, User_Pid, Type, ID, Header, Assignment} ->
    case length(Cars) of
      0 -> io:format(
             "No clients registered. Ignoring assignment.~n",[]);
      _ -> io:format(
              "Received assignment from user:~p~n",
              [{User_Pid, Type, ID, Header, Assignment}]),
           Config = {User_Pid, Type, ID, Header, Assignment},
           % assignment_handler() takes care of the assignment
           spawn_link(
             ?MODULE, assignment_handler, [Cars, Config, self()])
    end,
    cloud(Cars);

  % aggregated results
  {result, User_Pid, Type, ID, Header, Data} ->
    io:format("Received aggregated result~n", []),
    User_Pid ! {results, Type, ID, Header, Data},
    cloud(Cars)

  end.


% takes care of sending assignments to cars and waits for results
% right now it is assumed that all processes complete
assignment_handler(Cars, Config, Cloud_Pid) ->

  {User_Pid, Type, ID, Header, Assignment} = Config,

  Dataset = proplists:get_value("dataset", Assignment, ""),
  case Dataset of
    null ->  % key exists in proplist, but no value is set
      erlang:error(dataset_is_null);
    _ ->
      ok
  end,
  case string:find(Dataset, "_cv") of
    nomatch ->
      rand:seed(exs1024s, {123, 123534, 345345});
    _ ->
      noseed
  end,

  Pids = lists:map(fun({X, _}) -> X end, Cars),
  Result =
    case Type of
      "PingPong" ->
        lists:map(fun(X) ->
               X ! {assignment_car, self(), Type, ID, Assignment, none} end, Pids),
        % block until all results are received
        _Vals = [receive {result_edge, Pid, Data} -> Data end || Pid <- Pids],
        pong;

      "FedAvg" ->
        {Time, _, _} = Header,

        % send an init call to all clients
        {struct, Init_Clients} = proplists:get_value("init_clients", Assignment),
        Init_Assignment = [{"type", "init_ann"}, {"dataset", Dataset} | Init_Clients],
        [Pid ! {init_fed_avg_assignment_car, ID, Init_Assignment} || Pid <- Pids],

        % Returns a model
        Log_Name = make_FedAvg_log_string(Assignment, Time),

        Return_Model = update_weights_iter(Pids, Type, ID, Log_Name, Assignment),

        % Clean up some state on clients
        [Pid ! {finish_fed_avg_assignment_car, ID} || Pid <- Pids],

        Return_Model;

      "COOP" ->
        Model = get_random_model(Assignment),
        {Time, _, _} = Header,

        initialise_coop(Pids, Type, ID, Assignment, Model),

        Com_Rounds = proplists:get_value("communication_rounds", Assignment),
        Train_Time = proplists:get_value("train_time", Assignment),
        Start_Time = utils:get_timestamp(),
        Report_Freq = proplists:get_value("report_frequency", Assignment),

        Log_Name = make_COOP_log_string(Assignment, Time),
        Return_Model = coop_loop(Model, Log_Name, ID, Dataset, 1, Report_Freq, Com_Rounds, Train_Time, Start_Time),

        lists:foreach(fun(P) -> P ! {finish_coop_assignment_car, ID, self()} end, Pids),

        {{Year,Month,Day},{Hour,Min,_Sec}} = calendar:local_time(),
        Log_Path =
          list_to_binary(
            io_lib:format(
              "logs/complete_counter_log_~p-~p-~p_~p-~p.txt",[Year,Month,Day,Hour,Min])),

        OrderF = fun({_, NameX},{_, NameY}) -> NameX =< NameY end,
        Sorted_Cars = lists:sort(OrderF, Cars),

        Write_Count = fun({_Pid, Car_Name}) ->
          receive {counter_vals, Car_Name, N_Too_Old, N_Too_Often, N_Normal} ->
            Data = list_to_binary(
                io_lib:format(
                  "Car ~p - outdated: ~p, overactive: ~p, normal: ~p~n"
                  , [Car_Name, N_Too_Old, N_Too_Often, N_Normal])),
            file:write_file(Log_Path, Data, [append])
          after 10000 ->
            Data = list_to_binary(io_lib:format("Car ~p could not be reached in time.~n", [Car_Name])),
            file:write_file(Log_Path, Data, [append])
          end
        end,
        % Write counter logs with the 3 states of CO-OP for each car
        lists:foreach(Write_Count, Sorted_Cars),

        Return_Model;

      "FSVRG" ->
        {Time, _, _} = Header,

        % send an init call to all clients
        Step_Size = proplists:get_value("step_size", Assignment),
        Init_Assignment = [{"type", "init_svrg_ann"}, {"dataset", Dataset}, {"step_size", Step_Size}],
        [Pid ! {init_fed_avg_assignment_car, ID, Init_Assignment} || Pid <- Pids],

        Log_Name = make_FSVRG_log_string(Assignment, Time),

        Model = get_random_model(Assignment),

        Com_Rounds = proplists:get_value("communication_rounds", Assignment),
        Train_Time = proplists:get_value("train_time", Assignment),
        Start_Time = utils:get_timestamp(),

        Return_Model = fsvrg_loop(Com_Rounds, Start_Time, Train_Time
                          , Pids, Type, ID, Log_Name, Assignment, Model),

        % Clean up some state on clients
        [Pid ! {finish_fed_avg_assignment_car, ID} || Pid <- Pids],

        Return_Model
    end,

  % send aggregated results to server
  Cloud_Pid ! {result, User_Pid, Type, ID, Header, Result}.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Federated Stochastic Variance Reduced Gradient
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

fsvrg_loop(Communication_Rounds, Start_Time, Train_Time
      , Pids, Type, ID, Log_Name, Assignment, Model) ->
  Dataset = proplists:get_value("dataset", Assignment),

  % Compute full batch gradient
  {_Loss, _Metric, {Grads_W, Grads_B}} = verify_model(Model, "fsvrg", Dataset, Log_Name, ID),
  New_Ass = [{gradients_w, Grads_W}, {gradients_b, Grads_B} | Assignment],

  % Get all updated clients models
  % send Gradients, and edit clients.erl to do the computation.
  lists:foreach(fun(X) -> X ! {assignment_car, self(), Type, ID, New_Ass, Model} end, Pids),
  {Updated_Models, N_k_sum} = receive_model_updates(Pids),

  % Average Models
  AvgModel = model_avg(Updated_Models, N_k_sum),

  Time_Left = Train_Time - (utils:get_timestamp() - Start_Time),
  case Communication_Rounds =< 1 andalso Time_Left =< 0 of
    true ->
      {Loss_, Metric_} = verify_model(AvgModel, "verification", Dataset, Log_Name, ID),
      io:format("Final loss is ~p, and final metric is ~p.~n", [Loss_, Metric_]),
      io:format("Done!~n"),
      AvgModel;

    false ->
      io:format("~p C.R. and ~p seconds left.~n", [Communication_Rounds-1, Time_Left]),

      % Recurse without gradients
      fsvrg_loop(Communication_Rounds-1, Start_Time, Train_Time, Pids
        , Type, ID, Log_Name, Assignment, AvgModel)
  end.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Federated Averaging
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

update_weights_iter(Pids, Type, ID, Log_Name, Assignment) ->
  Dataset = proplists:get_value("dataset", Assignment),
  Model = get_random_model(Assignment),

  K = length(Pids),
  C = proplists:get_value("C", Assignment),
  CK = max(floor(C*K), 1),

  Total_Num_Data =
    case Dataset of
      "MNIST" ->
        get_mnist_n(K);
      "MNIST-non-iid" ->
        get_non_idd_mnist_n(K);
      Unknown ->
        {unknown_dataset, [Unknown]}
    end,

  Com_Rounds = proplists:get_value("communication_rounds", Assignment),
  Train_Time = proplists:get_value("train_time", Assignment),
  Start_Time = utils:get_timestamp(),

  update_weights_iter(Com_Rounds, Start_Time, Train_Time, Pids, K, CK, Total_Num_Data
            , Type, ID, Log_Name, Assignment, Model, maps:new(), maps:new()).


update_weights_iter(Communication_Rounds, Start_Time, Train_Time
      , Pids, K, CK, Total_Num_Data, Type, ID, Log_Name, Assignment, Model, Models_Map, N_k_Map) ->
  M_Clients = take_n_without_replacement(CK, Pids),
  io:format("Chosen clients: ~w~n", [M_Clients]),

  lists:map(fun(X) ->
         X ! {assignment_car, self(), Type, ID, Assignment, Model} end, M_Clients),
  io:format("Sending model.~n", []),

  Dataset = proplists:get_value("dataset", Assignment),
  {Loss, Metric} = verify_model(Model, "verification", Dataset, Log_Name, ID),
  io:format("Loss is ~p, and metric is ~p.~n", [Loss, Metric]),

  Variant = proplists:get_value("variant", Assignment),
  case Variant of
    "0" ->
      % block until all results are received
      {Updates, N_k_sum} = receive_model_updates(M_Clients),

      % Compute new global model and recurse
      AvgModel = model_avg(Model, Updates, Total_Num_Data, N_k_sum),

      {Updated_Map, Updated_N_k_Map} = {Models_Map, N_k_Map};

    "1" ->
      % block until all results are received
      {Updates, N_k_sum} = receive_model_updates(M_Clients),

      AvgModel = model_avg(Updates, N_k_sum),

      {Updated_Map, Updated_N_k_Map} = {Models_Map, N_k_Map};

    "2" ->
      % block until all results are received
      {Updated_Map, Updated_N_k_Map} = receive_model_updates_map(M_Clients, Models_Map, N_k_Map),
      Updated_Models = maps:values(Updated_Map),
      N_k_sum = lists:sum(maps:values(Updated_N_k_Map)),

      % Compute new global model and recurse
      AvgModel = model_avg(Updated_Models, N_k_sum)
  end,

  Time_Left = Train_Time - (utils:get_timestamp() - Start_Time),
  CR_Left = Communication_Rounds-1,
  case CR_Left =< 0 andalso Time_Left =< 0 of
    true ->
      {Loss_, Metric_} = verify_model(AvgModel, "verification", Dataset, Log_Name, ID),
      io:format("Final loss is ~p, and final metric is ~p.~n", [Loss_, Metric_]),
      AvgModel;
    false ->
      io:format("~p C.R. and ~p seconds left.~n", [CR_Left, Time_Left]),
      update_weights_iter(CR_Left, Start_Time, Train_Time, Pids, K, CK, Total_Num_Data
        , Type, ID, Log_Name, Assignment, AvgModel, Updated_Map, Updated_N_k_Map)
  end.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% CO-OP
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

initialise_coop(Pids, Type, ID, Assignment, Model) ->
  Bl = proplists:get_value("lower_age_limit", Assignment),
  Self = self(),
  register(age_tracker, spawn_link(fun() -> track_age(Bl, Self) end)),
  lists:foreach(fun(Pid) ->
    Pid ! {assignment_car, self(), Type, ID, Assignment, Model} end, Pids).


coop_loop(Server_Model, Log_Name, ID, Dataset
    , Counter, Report_Freq, Termination_Criterion, Train_Time, Start_Time) ->
  receive
    {model_request, Pid} ->
      age_tracker ! {get_age, self()},
      Age = receive {current_age, A} -> A end,
      Pid ! {model_and_age, {Age, Server_Model}},
      coop_loop(Server_Model, Log_Name, ID, Dataset
        , Counter, Report_Freq, Termination_Criterion, Train_Time, Start_Time);

    {coop_client_update, Pid, Client_Age, Model} ->

      age_tracker ! {get_and_increment_age, self()},
      Age = receive {current_age, A} -> A end,

      Alpha = 1 / math:sqrt(Age - Client_Age + 1),
      {Ws_S, Bs_S} = scale_model(Server_Model, (1-Alpha)),
      {Ws_C, Bs_C} = scale_model(Model, Alpha),

      % Add the weighted model parameters
      Updated_Ws = parameter_addition(Ws_S, Ws_C),
      Updated_Bs = parameter_addition(Bs_S, Bs_C),
      Updated_Model = {Updated_Ws, Updated_Bs},

      Pid ! {model_and_age, {Age+1, Updated_Model}},
      io:format("Update model: #~p~n", [Counter]),
      if
        Counter rem Report_Freq == 0 ->
          Score = verify_model(Updated_Model, "verification", Dataset, Log_Name, ID),
          io:format("Verification score: ~p~n", [Score]);
        true ->
          keep_going
      end,
      case Counter / Report_Freq >= Termination_Criterion
          andalso utils:get_timestamp() - Start_Time >= Train_Time of
        true ->
          age_tracker ! stop,
          io:format("Done!~n"),
          Updated_Model;

        false ->
          coop_loop(Updated_Model, Log_Name, ID, Dataset
            , Counter+1, Report_Freq, Termination_Criterion, Train_Time, Start_Time)
      end
  end.


% A separate process is spawed with this function and registered
% under the name: 'age_tracker'
track_age(Age, Assignment_H) ->
  receive
    {get_age, Pid} ->
      Pid ! {current_age, Age},
      track_age(Age, Assignment_H);

    {get_and_increment_age, Assignment_H} ->
      Assignment_H ! {current_age, Age},
      track_age(Age + 1, Assignment_H);

    stop ->
      ok
  end.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Server-side computation
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

make_FSVRG_log_string(Assignment, Time) ->
  Dataset = proplists:get_value("dataset", Assignment),
  H = proplists:get_value("step_size", Assignment),

  list_to_binary(
    io_lib:format(
      "logs/score_log_id~p_~s_h~p.csv", [Time, Dataset, H])).


make_FedAvg_log_string(Assignment, Time) ->
  Dataset = proplists:get_value("dataset", Assignment),
  C = proplists:get_value("C", Assignment),
  {struct, Init_List} = proplists:get_value("init_clients", Assignment),
  E = proplists:get_value("E", Init_List),
  B = proplists:get_value("B", Init_List),
  LR = proplists:get_value("lr", Init_List),
  Decay = proplists:get_value("decay", Init_List),

  list_to_binary(
    io_lib:format(
      "logs/score_log_id~p_~s_C~p_E~p_B~p_LR~p_Decay~p.csv"
      , [Time, Dataset, C, E, B, LR, Decay])).


make_COOP_log_string(Assignment, Time) ->
  Dataset = proplists:get_value("dataset", Assignment),
  B_l = proplists:get_value("lower_age_limit", Assignment),
  B_u = proplists:get_value("upper_age_limit", Assignment),
  {struct, Init_List} = proplists:get_value("init_clients", Assignment),
  E = proplists:get_value("E", Init_List),
  B = proplists:get_value("B", Init_List),
  LR = proplists:get_value("lr", Init_List),
  Decay = proplists:get_value("decay", Init_List),

  list_to_binary(
    io_lib:format(
      "logs/score_log_id~p_~s_Bl~p_Bu~p_E~p_B~p_LR~p_Decay~p.csv"
      , [Time, Dataset, B_l, B_u, E, B, LR, Decay])).


verify_model(Model, Type, Dataset, Log_Name, ID) ->
  Type_Key = {"type", Type},
  Data_Key = {"dataset", Dataset},
  Log_Path_Name = {"path_name", Log_Name},
  Json_Model = utils:model_to_json(Model),
  Model_Key = {"model", Json_Model},
  JSON = mochijson:encode({struct, [Type_Key, Data_Key, Log_Path_Name, Model_Key]}),

  ID_Str = integer_to_list(ID),
  Path_Name = "state/cloud/verification_model_id"++ID_Str++".json",
  Tmp_Path = Path_Name ++ "_tmp_",
  ok = file:write_file(Tmp_Path, JSON),
  ok = file:rename(Tmp_Path, Path_Name),

  Score_File_Name = "state/cloud/verification_score_id"++ID_Str++".json",
  Score = await_results(Score_File_Name),

  Loss = proplists:get_value("loss", Score),
  Metric = proplists:get_value("metric", Score),
  Ret =
    case Type of
      "fsvrg" ->
        Gradients_W = proplists:get_value("gradients_w", Score),
        Gradients_B = proplists:get_value("gradients_b", Score),
        {Loss, Metric, {Gradients_W, Gradients_B}};
      "verification" ->
        {Loss, Metric}
    end,

  ok = file:delete(Score_File_Name),
  Ret.


% A simple wait loop
await_results(FilenameIn) ->
  % check if results have been produced
  try
    case file:read_file(FilenameIn) of

      {ok, Data} ->
        Data,
        {_, Result} = mochijson:decode(Data),
        Result;

      % file not found
      _          ->
        timer:sleep(200),
        await_results(FilenameIn)
    end
  catch
    error:function_clause ->
      io:format("I Could not read json file. I'll try again.~n"),
      timer:sleep(100),
      await_results(FilenameIn)
  end.


% Print all connected node names in a sorted order
print_connections() ->
  Clients = nodes(connected),
  Compare = fun(A, B) ->
    A_Str = atom_to_list(A),
    B_Str = atom_to_list(B),
    A_Int = extract_first_integer(A_Str),
    B_Int = extract_first_integer(B_Str),
    A_Int =< B_Int
  end,
  Sorted = lists:sort(Compare, Clients),
  lists:foreach(fun(E) -> io:format("~p~n", [E]) end, Sorted).


% Converts "car11@10.0.2.15" to 11
% , "user@10.0.2.15" to 10
% , and "two" to -1
extract_first_integer(String) -> extract_first_integer(String, []).

extract_first_integer([], []) -> -1;
extract_first_integer([H|T], Int) when (H >= $0) and (H =< $9) ->
  extract_first_integer(T, Int ++ [H]);
extract_first_integer([_H|T], []) ->
  extract_first_integer(T, []);
extract_first_integer(_, Int) ->
  list_to_integer(Int).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Get Subset of clients
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

take_n_without_replacement(N, X) ->
  Y = shuffle(X),
  lists:sublist(Y, N).


shuffle(X) ->
  [Y||{_,Y} <- lists:sort([ {rand:uniform(), N} || N <- X])].



%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Repeat receives
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

receive_model_updates(Pids) ->
  receive_model_updates(Pids, [], 0).


receive_model_updates([], Models, N_k_sum) ->
  {Models, N_k_sum};
receive_model_updates([Pid | Pids], Models, N_k_sum) ->
  {Model_k, N_k}  = receive {result_edge, Pid, Data} -> Data end,
  Scaled_Model_k = scale_model(Model_k, N_k),
  receive_model_updates(Pids, [Scaled_Model_k | Models], N_k_sum + N_k).



receive_model_updates_map([], Models_Map, N_k_Map) ->
  {Models_Map, N_k_Map};
receive_model_updates_map([Pid | Pids], Models_Map, N_k_Map) ->
  {Model_k, N_k}  = receive {result_edge, Pid, Data} -> Data end,
  Scaled_Model_k = scale_model(Model_k, N_k),
  Updated_Model_Map = maps:put(Pid, Scaled_Model_k, Models_Map),
  Updated_N_k_Map = maps:put(Pid, N_k, N_k_Map),

  receive_model_updates_map(Pids, Updated_Model_Map, Updated_N_k_Map).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Model arithmetics
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Average updated models
model_avg(Updated_Models, N) ->
  % Assume that the server has already scaled local models
  {U_Layers, U_Biases} = lists:unzip(Updated_Models),

  [Ws_0 | U_Layers_tl] = U_Layers,
  [Bs_0 | U_Biases_tl] = U_Biases,

  Acc_Fun = fun(Ps, Acc) -> parameter_addition(Ps, Acc) end,
  Sum_Ws = lists:foldr(Acc_Fun, Ws_0, U_Layers_tl),
  Sum_Bs = lists:foldr(Acc_Fun, Bs_0, U_Biases_tl),

  % Divide to yield an average
  Div_Scalar = 1/N,
  Avg_Ws = scale_parameters(Sum_Ws, Div_Scalar),
  Avg_Bs = scale_parameters(Sum_Bs, Div_Scalar),

  {Avg_Ws, Avg_Bs}.


% Average updated models and weight them against the current model.
% N_k_sum is the number of datapoints that updated the models, while
% N is the total sum over all clients
model_avg(Model, Updated_Models, N, N_k_sum) ->
  % Assume that the server has already scaled local models
  Scalar = N-N_k_sum, % Weighting factor for the central model
  {Ws0, Bs0} = Model,
  Ws = scale_parameters(Ws0, Scalar), % Potential parallelism here
  Bs = scale_parameters(Bs0, Scalar),

  Extended_Updated_Models = [{Ws, Bs} | Updated_Models],
  model_avg(Extended_Updated_Models, N).


parameter_addition(P1, P2) ->
  Add_Weights = fun(X,Y) -> X+Y end,
  Add_Layers = fun(Xs, Ys) -> lists:zipwith(Add_Weights, Xs, Ys) end,
  lists:zipwith(Add_Layers, P1, P2).


% Multiply all parameters of an ANN model with Scalar
scale_model({Ws, Bs}, Scalar) ->
  Scaled_Ws = scale_parameters(Ws, Scalar),
  Scaled_Bs = scale_parameters(Bs, Scalar),
  %io:format("Scaled local model:  ~p ~p ~n", [Scaled_Ws, Scaled_Bs]),
  {Scaled_Ws, Scaled_Bs}.


% Multiply all values in a list of lists with Scalar
scale_parameters(Params, Scalar) ->
  Scale_Fun = fun(Xs) -> lists:map(fun(X) -> X*Scalar end, Xs) end,
  lists:map(Scale_Fun, Params).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Randomly initialized models
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

get_random_model(Assignment) ->
  Dataset = proplists:get_value("dataset", Assignment),
  _Model =
    case Dataset of
      undefined ->
        erlang:error(missing_property, ["dataset"]);
      null ->
        erlang:error(dataset_is_null);
      _MNIST -> % We only use MNIST data right now
        random_mnist_model()
    end.


random_mnist_model() ->
  random_fc_model([28*28,200,200,10]).


random_fc_model([_N_Neurons]) -> {[],[]};
random_fc_model(N_Neurons_List) ->
  % N_Neurons_List is the number of neurons for each layer
  Layer_1 = hd(N_Neurons_List), % Number of neurons for a layer
  Next_Layers = tl(N_Neurons_List),
  Layer_2 = hd(Next_Layers), % Number of neurons for the next layer

  N_Of_W = Layer_1*Layer_2,
  N_Of_B = Layer_2,

  W1 = [rand:normal(0, 0.003) || _ <- lists:seq(1, N_Of_W)],
  B1 = [rand:normal(0, 0.003) || _ <- lists:seq(1, N_Of_B)],

  {Ws, Bs} = random_fc_model(Next_Layers),
  {[W1 | Ws], [B1 | Bs]}.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Get static n
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

get_non_idd_mnist_n(K) ->
  Dir_Path = "data/mnist-non-iid/",
  Filenames = [Dir_Path ++ "car" ++ integer_to_list(Id) ++ "-labels.byte"|| Id <- lists:seq(1, K)],
  N_ks = [get_n_k_from_mnist_file(F) || F <- Filenames],
  lists:sum(N_ks).


get_mnist_n(K) ->
  Dir_Path = "data/mnist/",
  Filenames = [Dir_Path ++ "car" ++ integer_to_list(Id) ++ "-labels.byte"|| Id <- lists:seq(1, K)],
  N_ks = [get_n_k_from_mnist_file(F) || F <- Filenames],
  lists:sum(N_ks).


get_n_k_from_mnist_file(File_Name) ->
    File = file:read_file(File_Name),
    {ok, Bin} = File,
    Len_Bin = binary:part(Bin, {4,4}),
    <<Len:4/big-unsigned-integer-unit:8>> = Len_Bin,
    Len.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Kill nodes. Useful to kill simulatios with many clients.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

exit_simulation() ->
  exit_python(),
  exit_nodes(),
  init:stop().


exit_python() ->
  Cars = nodes(hidden),
  io:format("~p", [Cars]),
  {_, BadCars} = rpc:multicall(Cars, os, cmd, ["pkill python3"]),

  [io:format("RPC to ~p failed. Python hasn't been killed. ~n", [BadCar])
    || BadCar <- BadCars],
  [io:format("Python kill-message sent to: ~p~n", [Car]) || Car <- Cars -- BadCars].


exit_nodes() ->
  rpc:multicall(nodes(connected), init, stop, []).
