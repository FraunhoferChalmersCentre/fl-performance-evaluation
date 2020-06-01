-module(clients).
-export([
  car/2,
  edge_handler/7,
  edge_handler_indef/9
]).


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Car (Client)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% the car process filters incoming sensor values and only transmits a
% subset to the server process ("cloud")
% arguments:
%   Cloud_Node: PID of cloud process
%   Name      : name of car process
car(Cloud_Node, Name) ->

  receive

  {init_fed_avg_assignment_car, ID, Init_Assignment} ->
    initiate_ann(Name, ID, Init_Assignment);

  {finish_fed_avg_assignment_car, ID} ->
    destroy_ann(Name, ID);

  {finish_coop_assignment_car, ID, From} ->
    CoopID = list_to_atom("coop" ++ integer_to_list(ID)),
    CoopID ! {destroy_ann, Name, ID, From};

  {assignment_car, Handler_Pid, "COOP", ID, Assignment, Model} ->
    % Initilise an ANN on the python side
    {struct, Init_Clients} = proplists:get_value("init_clients", Assignment),
    Dataset = proplists:get_value("dataset", Assignment),
    Init_Assignment = [{"type", "init_ann"}, {"dataset", Dataset} | Init_Clients],
    initiate_ann(Name, ID, Init_Assignment),

    register(counter, spawn_link(fun() -> counter_process(0,0,0, Name) end)),
    CoopID = list_to_atom("coop" ++ integer_to_list(ID)),
    register(CoopID, spawn_link(?MODULE, edge_handler_indef, [Cloud_Node, self(), Handler_Pid
      , "COOP", ID, Name, Assignment, 0, Model]));

  % receive assignment from assignment_handler
  {assignment_car, Handler_Pid, Type, ID, Assignment, Model} ->

    % await results (spawn process)
    spawn_link(?MODULE, edge_handler, [self(), Handler_Pid, Type, ID, Name, Assignment, Model])

  end,

  car(Cloud_Node, Name).


edge_handler(Car_Pid, Assignment_Handler_Pid, Type, ID, Name, Assignment, Model) ->

  % write to JSON; input is of form {struct, PropList}
  io:format("Writing JSON.~n", []),

  Assign1 = [{"type", Type} | Assignment],
  Assign2 =
    case Type of
      "FedAvg" ->
        [{"model", utils:model_to_json(Model)} | Assign1];

      "FSVRG" ->
        [{"model", utils:model_to_json(Model)} | Assign1];

      _ ->
        Assign1
    end,
  JSON = mochijson:encode({struct, Assign2}),
  % Now a Python process takes over to do the assigned task

  % It is not strictly necessary to add the car name to the file, but
  % when simulating multiple cars on one machine, it is necessary
  FilePathOut = output_assignment_file_name(Name, ID),
  write_file(FilePathOut, JSON),

  % this file is produced by a Python process that is executed on the
  % edge
  FilenameIn = input_assignment_file_name(Name, ID),

  % Wait for the right file to appear in state/edge_in/
  {_, Xs} = await_results(FilenameIn, ID),

  Val =
    case Type of
      "FedAvg" ->
        {_, Params} = proplists:get_value("result", Xs),
        W_Json = proplists:get_value("w", Params),
        B_Json = proplists:get_value("b", Params),
        N_k= proplists:get_value("n_k", Params),
        Ws = json_array_to_list_of_lists(W_Json),
        Bs = json_array_to_list_of_lists(B_Json),
        {{Ws, Bs}, N_k};


      "FSVRG" ->
        {_, Params} = proplists:get_value("result", Xs),
        W_Json = proplists:get_value("w", Params),
        B_Json = proplists:get_value("b", Params),
        N_k= proplists:get_value("n_k", Params),
        Ws = json_array_to_list_of_lists(W_Json),
        Bs = json_array_to_list_of_lists(B_Json),
        {{Ws, Bs}, N_k};


      _ ->
        proplists:get_value("result", Xs)
    end,
  io:format("Found a result~n"),

  Assignment_Handler_Pid ! {result_edge, Car_Pid, Val},

  % delete file after reading
  % (Python module should NOT delete any files)
  % TODO: let edge_handler remove both files
  ok = file:delete(FilenameIn),
  io:format("Deleting: ~p~n", [FilenameIn]).


% An indefinite edge handler, used by CO-OP
edge_handler_indef(Cloud_Node, Car_Pid, Assignment_H, Type, ID, Name, Assignment
  , Age, Model) ->

  write_assignment(Type, ID, Name, Assignment, Model),
  Trained_Model = wait_for_updated_model(Name, ID),

  Server_Age = request_age(Cloud_Node),
  io:format("Age: ~p~nServer age: ~p~n~n", [Age, Server_Age]),

  Bl = proplists:get_value("lower_age_limit", Assignment),
  Bu = proplists:get_value("upper_age_limit", Assignment),

  case age_check(Server_Age, Age, Bl, Bu) of
    too_old ->
      {New_Age, New_Model} = reconcile_with_server(Assignment_H),
      counter ! inc_too_old,
      edge_handler_indef(Cloud_Node, Car_Pid, Assignment_H, Type, ID, Name
        , Assignment, New_Age, New_Model);

    too_often ->
      counter ! inc_too_often,
      edge_handler_indef(Cloud_Node, Car_Pid, Assignment_H, Type, ID, Name
        , Assignment, Age, Model);

    normal ->
      counter ! inc_normal,
      {New_Age, New_Model} = coop_upload(Assignment_H, Age, Trained_Model),

      edge_handler_indef(Cloud_Node, Car_Pid, Assignment_H, Type, ID, Name
        , Assignment, New_Age, New_Model)

  end.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% CO-OP utilites
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% This should get the server's model and age.
reconcile_with_server(Assignment_H) ->
  Assignment_H ! {model_request, self()},
  super_receive(model_and_age).


% Upload to server for merging and wait for updated model
coop_upload(Assignment_H, Age, Model) ->
  Assignment_H ! {coop_client_update, self(), Age, Model},
  super_receive(model_and_age).


super_receive(Match_Atom) ->
  receive
    {Match_Atom, Return_Val} ->
      Return_Val;
    {destroy_ann, Name, ID, From} ->
      % print a log
      counter ! {print_and_stop, From},
      destroy_ann(Name, ID),
      exit(normal)
  end.


age_check(A, Ak, Bl, Bu) ->
  Diff = A - Ak,
  if
    Diff > Bu -> too_old;
    Diff < Bl -> too_often;
    true -> normal
  end.


request_age(Cloud_Node) ->
  {age_tracker, Cloud_Node} ! {get_age, self()},
  super_receive(current_age).


write_assignment(Type, ID, Name, Assignment, Model) ->
  Assign1 = [{"type", Type} | Assignment],
  Assign2 =
    case Type of
      %"FedAvg" or "COOP" ->
      "COOP" ->
        [{"model", utils:model_to_json(Model)} | Assign1];

      _ ->
        Assign1
    end,
  JSON = mochijson:encode({struct, Assign2}),
  % Now a Python process takes over to do the assigned task

  % It is not strictly necessary to add the car name to the file, but
  % when simulating multiple cars on one machine, it is necessary
  FilePathOut = output_assignment_file_name(Name, ID),

  write_file(FilePathOut, JSON).


wait_for_updated_model(Name, ID) ->
  % this file is produced by a Python process that is executed on the edge
  FilenameIn = input_assignment_file_name(Name, ID),

  % Wait for the right file to appear in state/edge_in/
  {_, Xs} = await_results(FilenameIn, ID),

  {_, Params} = proplists:get_value("result", Xs),
  W_Json = proplists:get_value("w", Params),
  B_Json = proplists:get_value("b", Params),
  Ws = json_array_to_list_of_lists(W_Json),
  Bs = json_array_to_list_of_lists(B_Json),

  % Remove assignment after results have been read
  ok = file:delete(FilenameIn),
  io:format("Deleting: ~p~n", [FilenameIn]),

  {Ws, Bs}.


counter_process(N_Too_Old, N_Too_Often, N_Normal, Car_Name) ->
  receive
    inc_too_old ->
      counter_process(N_Too_Old + 1, N_Too_Often, N_Normal, Car_Name);
    inc_too_often ->
      counter_process(N_Too_Old, N_Too_Often + 1, N_Normal, Car_Name);
    inc_normal ->
      counter_process(N_Too_Old, N_Too_Often, N_Normal + 1, Car_Name);
    {print_and_stop, From} ->
      From ! {counter_vals, Car_Name, N_Too_Old, N_Too_Often, N_Normal},
      % Format data
      Data = list_to_binary(
                io_lib:format(
                  "car~p: too old: ~p, too often: ~p, normal ~p~n"
                  , [Car_Name, N_Too_Old, N_Too_Often, N_Normal])),
      io:format(Data),
      % Write to file
      {{Year,Month,Day},{Hour,Min,_Sec}} = calendar:local_time(),
      Log_Path =
        list_to_binary(
          io_lib:format(
            "logs/counter_log_~p-~p-~p_~p:~p.txt",[Year,Month,Day,Hour,Min])),
      file:write_file(Log_Path, Data, [append])
  end.


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Misc.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% Initilise an ANN on the python side
initiate_ann(Name, ID, Init_Assignment) ->
  File_Name = output_assignment_file_name(Name, ID),
  JSON = mochijson:encode({struct, Init_Assignment}),
  write_file(File_Name, JSON).


destroy_ann(Name, ID) ->
  File_Name = output_assignment_file_name(Name, ID),
  Destructive_Ass = {struct, [{"type", "destroy_ann"}]},
  JSON = mochijson:encode(Destructive_Ass),
  write_file(File_Name, JSON).


% Returns a relative path
output_assignment_file_name(Name, ID) ->
  DirOut      = "state/edge_out/",
  FilenameOut = "assignment_car_" ++ integer_to_list(Name)
             ++ "_id_" ++ integer_to_list(ID) ++ ".json",
  DirOut ++ FilenameOut.


% Returns a relative path
input_assignment_file_name(Name, ID) ->
  DirIn    = "./state/edge_in/",
  Results  = "edge_result_car_" ++ integer_to_list(Name)
             ++ "_id_" ++ integer_to_list(ID) ++ ".json",
  DirIn ++ Results.


% Write a file if it does not exist
% , otherwise keep await uńtil the file is deleted
write_file(File_Name, Data) ->
  case filelib:is_file(File_Name) of
    false ->
      % write file
      Tmp_Path = File_Name ++ "_tmp_",
      {ok, IoDevice} = file:open(Tmp_Path, [write]),
      ok = file:write(IoDevice, Data),
      ok = file:close(IoDevice),
      ok = file:rename(Tmp_Path, File_Name);
    true ->
      timer:sleep(200),
      write_file(File_Name, Data)
  end.


% A simple wait loop
await_results(FilenameIn, ID) ->
  % check if results have been produced
  try
    case file:read_file(FilenameIn) of

      {ok, Data} ->
        Data,
        mochijson:decode(Data);

      % file not found
      _          ->
        %io:format("Waiting for results (ID: ~p)~n", [ID]),
        timer:sleep(3000),
        await_results(FilenameIn, ID)
    end
  catch
    error:function_clause ->
      io:format("I Could not read json file. I'll try again.~n"),
      timer:sleep(100),
      await_results(FilenameIn, ID)
  end.


json_array_to_list({array, List}) ->
  List.


json_array_to_list_of_lists({array, ListOfLists}) ->
  [json_array_to_list(X) || X <- ListOfLists].
