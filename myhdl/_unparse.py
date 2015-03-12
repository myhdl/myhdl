#  This file is part of the myhdl library, a Python package for using
#  Python as a Hardware Description Language.
#
#  Copyright (C) 2003-2008 Jan Decaluwe
#
#  The myhdl library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public License as
#  published by the Free Software Foundation; either version 2.1 of the
#  License, or (at your option) any later version.
#
#  This library is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#  Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public
#  License along with this library; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

""" unparse module

"""


import compiler
from cStringIO import StringIO

def _unparse(ast):
    v = _UnparseVisitor()
    compiler.walk(ast, v)
    return v.buf.getvalue()

class _UnparseVisitor(object):
    
    def __init__(self):
        self.buf = StringIO()

    def write(self, arg):
        self.buf.write(arg)

    def unaryOp(self, node, op):
        self.write("(")
        self.write("%s" % op)
        self.visit(node.expr)
        self.write(")")

    def binaryOp(self, node, op):
        self.write("(")
        self.visit(node.left)
        self.write(" %s " % op)
        self.visit(node.right)
        self.write(")")
    
    def multiOp(self, node, op):
        self.write("(")
        self.visit(node.nodes[0])
        for node in node.nodes[1:]:
            self.write(" %s " % op)
            self.visit(node)
        self.write(")")
    
    def visitAdd(self, node):
        self.binaryOp(node, '+')
        
    def visitAnd(self, node):
        self.multiOp(node, ' and ')
        
    def visitBitand(self, node):
        self.multiOp(node, '&')
        
    def visitBitor(self, node):
        self.multiOp(node, '|')
         
    def visitBitxor(self, node):
        self.multiOp(node, '^')

    def visitCallFunc(self, node):
        self.visit(node.node)
        self.write('(')
        comma = ''
        for arg in node.args:
            self.write(comma); comma=','
            self.visit(arg)
        if node.star_args:
            self.write(comma); comma=','
            self.write('*')
            self.visit(node.star_args)
        if node.dstar_args:
            self.write(comma); comma=','
            self.write('**')
            self.visit(node.dstar_args)
        self.write(')')
        
    def visitCompare(self, node):
        self.write("(")
        self.visit(node.expr)
        for comp in node.ops:
            op, expr = comp
            self.write(" %s " % op)
            self.visit(expr)
        self.write(")")
        
    def visitConst(self, node):
        self.write(str(node.value))

    def visitGetattr(self, node):
        self.visit(node.expr)
        self.write('.')
        self.write(node.attrname)

    def visitFloorDiv(self, node):
        self.binaryOp(node, '//')

    def visitInvert(self, node):
        self.unaryOp(node, '~')

    def visitKeyword(self, node):
        self.write(node.name)
        self.write('=')
        self.visit(node.expr)
        
    def visitLeftShift(self, node):
        self.binaryOp(node, '<<')

    def visitName(self, node):
        self.write(node.name)

    def visitMod(self, node):
        self.binaryOp(node, '%')

    def visitMul(self, node):
        self.binaryOp(node, '*')

    def visitNot(self, node):
        self.unaryOp(node, 'not ')

    def visitOr(self, node):
        self.multiOp(node, ' or ')

    def visitPower(self, node):
        self.binaryOp(node, '**')
    
    def visitRightShift(self, node):
        self.binaryOp(node, '>>')

    def visitSlice(self, node):
        self.visit(node.expr)
        self.write('[')
        if node.lower is not None:
            self.visit(node.lower)
        self.write(':')
        if node.upper is not None:
            self.visit(node.upper)
        self.write(']')
        
    def visitSub(self, node):
        self.binaryOp(node, '-')
        
    def visitSubscript(self, node):
        self.visit(node.expr)
        self.write("[")
        if len(node.subs) > 1:
            raise NotImplementedError
        self.visit(node.subs[0])
        self.write("]")
        
    def visitUnaryAdd(self, node, *args):
        self.unaryOp(node, '+')
        
    def visitUnarySub(self, node, *args):
        self.unaryOp(node, '-')
