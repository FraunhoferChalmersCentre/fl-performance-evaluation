%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% OODIDA Prototype: bare-bones version
% (Internal versions/quick prototyping)
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

-module(bridge).
-export([
  init_cloud/0,
  init_user/1,
  init_car/2
]).

-define(TICKTIME, 1800).

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Entry points
%%% cloud and user in different terminals, each car in separate terminal
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
init_cloud() ->
  process_flag(trap_exit, true),
  change_initiated = net_kernel:set_net_ticktime(?TICKTIME),
  ok = net_kernel:monitor_nodes(true, [nodedown_reason, {node_type, hidden}]),

  Cars  = [],
  register(cl0ud, spawn_link(server, cloud, [Cars])),

  listen("cloud").


init_user(Cloud_Node) ->
  process_flag(trap_exit, true),
  change_initiated = net_kernel:set_net_ticktime(?TICKTIME),

  register(us3r, spawn_link(users, user,[Cloud_Node])),
  io:format("user pid: ~p~n", [us3r]),
  net_kernel:connect_node(Cloud_Node),
  spawn_link(users, awaitJSON, [us3r]),

  listen("user").


% run in each terminal
init_car(Name, Cloud_Node) ->
  process_flag(trap_exit, true),
  change_initiated = net_kernel:set_net_ticktime(?TICKTIME),
  ok = net_kernel:monitor_nodes(true, [nodedown_reason, {node_type, hidden}]),

  Pid = spawn_link(clients, car, [Cloud_Node, Name]),
  {cl0ud, Cloud_Node} ! {new_car, Pid, Name},

  Car_Name = "car" ++ integer_to_list(Name),
  listen(Car_Name).


listen(Name) ->
  Ts = integer_to_list(utils:get_timestamp()),
  listen(Name, Ts).

% log error and terminate on exit signal
listen("cloud", Ts) ->
  receive
    {nodeup, _Node, _Info} ->
      listen("cloud", Ts);
    {nodedown, Node, Info} ->
      Reason = hd(Info),
      log_error("cloud", {Node, Reason}, Ts),
      net_adm:ping(Node),
      listen("cloud", Ts);
    {'EXIT', _Pid, Reason} ->
      log_error("cloud", Reason, Ts),
      init:stop() % kill the node if any linked process dies.
  end;

listen(Name, Ts) ->
  receive
    {nodeup, _Node, _Info} ->
      listen(Name, Ts);
    {nodedown, Node, Info} ->
      Reason = hd(Info),
      log_error(Name, {Node, Reason}, Ts),
      listen(Name, Ts);
    {'EXIT', _Pid, Reason} ->
      log_error(Name, Reason, Ts),
      init:stop() % kill the node if any linked process dies.
  end.


log_error(Name, Reason, Ts) ->
  Filename = "logs/" ++ Name ++"_crash_" ++ Ts ++ ".dump",
  {ok, S} = file:open(Filename, [append]),
  io:format(S, "~p~n", [Reason]),
  file:close(S).
