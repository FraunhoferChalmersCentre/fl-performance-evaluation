-module(utils).
-export([model_to_json/1, get_timestamp/0]).


%%% MochiJson:
%{struct,[{"result",
%          {struct, [{"w",{array, [{array, ...}, ...]}},
%                    {"b",{array, [{array, ...}, ...]}}
%                   ]
%          }
%        ]}
%%% JSON:
%{
%  "result": {
%    "w": [[0.20292915403842926, 0.25576138496398926, -0.3770759105682373, -0.04769778251647949, -0.23005855083465576, ...]],
%    "b": [[-0.04067124053835869, 0.0, -0.2195659875869751, 0.0, 0.1232801154255867], [-0.6181043386459351]]
%  }
%}

list_to_json_array(List) ->
  {array, List}.


list_of_lists_to_json_array(ListOfLists) ->
  {array, [list_to_json_array(X) || X <- ListOfLists]}.


model_to_json({Ws, Bs}) ->
  W_Json = list_of_lists_to_json_array(Ws),
  B_Json = list_of_lists_to_json_array(Bs),
  {struct, [{"w", W_Json}, {"b", B_Json}]}.


get_timestamp() ->
  {Mega, Sec, Micro} = os:timestamp(),
  Mega*1000000 + Sec + round(Micro/1000000).