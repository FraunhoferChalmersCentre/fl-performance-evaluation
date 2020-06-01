import os


def compile_all():
    os.system('erlc erlang_framework/bridge.erl')
    os.system('erlc erlang_framework/clients.erl')
    os.system('erlc erlang_framework/server.erl')
    os.system('erlc erlang_framework/users.erl')
    os.system('erlc erlang_framework/libs/utils.erl')
    os.system('erlc erlang_framework/libs/mochijson.erl')
    os.system('erlc erlang_framework/libs/mochinum.erl')

if __name__ == '__main__':
    compile_all()
