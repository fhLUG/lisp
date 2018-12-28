# -*- coding: utf-8 -*-

from .types import Environment, DiyLangError, Closure, String
from .ast import is_boolean, is_atom, is_symbol, is_list, is_closure, \
    is_integer, is_string
from .parser import unparse

"""
This is the Evaluator module. The `evaluate` function below is the heart
of your language, and the focus for most of parts 2 through 6.

A score of useful functions is provided for you, as per the above imports,
making your work a bit easier. (We're supposed to get through this thing
in a day, after all.)
"""


def evaluate(ast, env):
    """Evaluate an Abstract Syntax Tree in the specified environment."""

    if ast == []:
        raise DiyLangError('cannot evaluate empty expression')

    if is_symbol(ast):
        return env.lookup(ast)

    if is_atom(ast):
        return ast

    op = ast[0]

    if op == 'define':
        if len(ast) != 3:
            raise DiyLangError('Wrong number of arguments')
        name = ast[1]
        args = ast[2]

        if not is_symbol(name):
            raise DiyLangError('%s is not a symbol' % name)

        return env.set(name, evaluate(args, env))

    if op == 'lambda':
        if len(ast) != 3:
            raise DiyLangError('Wrong number of arguments')
        args = ast[1]
        body = ast[2]

        if not is_list(args):
            raise DiyLangError('lambda args must be a list')
        return Closure(env, args, body)

    if op == 'quote':
        return ast[1]

    if op == 'atom':
        return is_atom(evaluate(ast[1], env))

    if op == 'if':
        cond = evaluate(ast[1], env)
        if cond:
            return evaluate(ast[2], env)
        else:
            return evaluate(ast[3], env)

    math_result = eval_math(ast, env)
    if math_result is not None:
        return math_result

    if op == 'cons':
        (lhs, rhs) = eval(ast, env)
        if is_string(lhs) and is_string(rhs):
            return String(lhs.val + rhs.val)
        return [lhs] + rhs

    if op == 'head':
        l = evaluate(ast[1], env)
        if is_string(l):
            return String(l.val[0])

        if not is_list(l):
            raise DiyLangError('must be list to get head')
        if l == []:
            raise DiyLangError('list is empty')
        return l[0]

    if op == 'tail':
        l = evaluate(ast[1], env)
        if is_string(l):
            return String(l.val[1:])

        if not is_list(l):
            raise DiyLangError('must be list to get tail')
        if l == []:
            raise DiyLangError('list is empty')
        return l[1:]

    if op == 'empty':
        l = evaluate(ast[1], env)
        if is_string(l):
            return l.val == ''

        if not is_list(l):
            raise DiyLangError('must be list to test empty')

        return l == []

    if op == 'cond':
        conds = ast[1]
        for cond in conds:
            if evaluate(cond[0], env):
                return evaluate(cond[1], env)
        return False

    if op == 'let':
        let = env

        for binding in ast[1]:
            let = let.extend({ binding[0]: evaluate(binding[1], let ) })
            #let.set(binding[0], )

        return evaluate(ast[2], let)

    if op == 'defn':
        if len(ast) != 4:
            raise DiyLangError('Wrong number of arguments')
        name = ast[1]
        args = ast[2]
        body = ast[3]

        if not is_symbol(name):
            raise DiyLangError('%s is not a symbol' % (ast[1]))
        if not is_list(args):
            raise DiyLangError('lambda args must be a list')

        return env.set(name, Closure(env, args, body))

    # TODO something is broken here, we shouldn't need an extra eval_closure function, but should be able to use recursion, i.e. evaluate the first item until we have none of the above or a closure

    # special form: we already have a closure
    if is_closure(op):
        return eval_closure(op, ast[1:], env)

    # not one of the special forms => function call
    # first item: function
    # other items: args

    fun = evaluate(op, env)
    if not is_closure(fun):
        raise DiyLangError('%s is not a function' % fun)
    return eval_closure(fun, ast[1:], env)

    raise NotImplementedError("DIY")

def eval(ast, env):
    return evaluate(ast[1], env), evaluate(ast[2], env)

def check_math(lhs, rhs):
    if not is_integer(lhs) or not is_integer(rhs):
        raise DiyLangError('math only supported for numbers')

def eval_math(ast, env):
    op = ast[0]
    if op == 'eq':
        (lhs, rhs) = eval(ast, env)
        return is_atom(lhs) and is_atom(rhs) and lhs == rhs

    if op == '+':
        (lhs, rhs) = eval(ast, env)
        check_math(lhs, rhs)
        return lhs + rhs

    if op == '-':
        (lhs, rhs) = eval(ast, env)
        check_math(lhs, rhs)
        return lhs - rhs

    if op == '/':
        (lhs, rhs) = eval(ast, env)
        check_math(lhs, rhs)
        return lhs // rhs

    if op == '*':
        (lhs, rhs) = eval(ast, env)
        check_math(lhs, rhs)
        return lhs * rhs

    if op == 'mod':
        (lhs, rhs) = eval(ast, env)
        check_math(lhs, rhs)
        return lhs % rhs

    if op == '>':
        (lhs, rhs) = eval(ast, env)
        check_math(lhs, rhs)
        return lhs > rhs

    return None


def eval_closure(closure, args, env):
    formal_args = closure.params
    actual_args = [evaluate(arg, env) for arg in args]
    if len(formal_args) != len(actual_args):
        raise DiyLangError('wrong number of arguments, expected %d got %d' % (len(formal_args), len(actual_args)))

    inner_env = closure.env.extend(dict(zip(formal_args, actual_args)))
    return evaluate(closure.body, inner_env)
