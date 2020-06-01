#!/usr/bin/env escript

main([]) ->

  Ip = my_ip(),
  Name = list_to_atom("exitScript@" ++ Ip),
  {ok, _} = net_kernel:start([Name, 'longnames']),

  CloudName = list_to_atom("cloud@" ++ Ip),
  pong = net_adm:ping(CloudName),

  rpc:call(CloudName, server, exit_simulation, []),  

  ok;

main(_) ->
  usage().


usage() ->
  io:format("usage: rpc with an exit signal to all nodes in the simulation~n"),
  halt(1). % return non-zero exit code


my_ip() ->
 {Ip4, Ip3, Ip2, Ip1} = get_ip(),
 IpList = [integer_to_list(X) || X <- [Ip4, Ip3, Ip2, Ip1]],
 lists:concat(join(".", IpList)).


% Give the first IP that isn't the loopback address.
get_ip() ->
 {ok, Ifs} = inet:getifaddrs(),
 Addrs = [ lists:keyfind(addr, 1, Flags) || {_, Flags} <- Ifs],
 Ip = [ Ip || {addr, Ip} <- Addrs, size(Ip) == 4, Ip =/= {127,0,0,1}],
 hd(Ip).


join(Sep, Xs) ->
  join(Sep, Xs, []).
join(_, [], Acc) ->
  lists:reverse(Acc);
join(Sep, [X], Acc) ->
  join(Sep, [], [X | Acc]);
join(Sep, [X|Xs], Acc) ->
  join(Sep, Xs, [(X ++ Sep) | Acc]).
