
import argparse
def get_argparser():
    parser = argparse.ArgumentParser(description='shape annotation')
    parser.add_argument('--react',  type=str, nargs=1, default='data.react', help='react (>seqname\\n1\\t shapevalue\\n2\\t shapevalue etc)')
    parser.add_argument('--dbn',  type=str, nargs=1, default='data.dbn', help=' dbn files (>seqname\\nsequence\\ndotbacked etc)')
    parser.add_argument('--target',  type=str, nargs=1, default='target.dbn', help='we predict on these...  dbn files (>seqname\\nsequence\\ndotbacked etc)')
    parser.add_argument('--output',  type=str, nargs=1, default='out.react', help='we predict on these...  dbn files (>seqname\\nsequence\\ndotbacked etc)')
    parser.add_argument('--kernelargs',  type=dict, nargs=1, default={}, help='dictionary for the eden constructor.. UNUSED ')
    return parser



#####
# READ DATA
#####
def read_dbn(path):
    with open(path,'r') as fi:
        text = fi.read()
        text = text.split(">")[1:]
        res=[]
        for e in text:
            a_thing = [thing for thing in e.split('\n') if len(thing) > 1]
            if len(a_thing)!=3:
                print "ERRER", a_thing ,e
                return
            if len(a_thing[1])!=len(a_thing[2]):
                print "ERRER", a_thing ,e
                return
            res.append(a_thing)
    return res

def read_react(path):
    with open(path,'r') as fi:
        text = fi.read()
        text = text.split(">")[1:]
        res={}
        for e in text:
            lines = [thing for thing in e.split('\n') if len(thing) > 1]
            header = lines[0]
            data = [ e.strip().split() for e in lines[1:]  ]
            data = [ float(d[1].strip()) for d in data if len(d)==2 ]
            res[header.strip()] = data
    return res


def combine_dbn_react(dbn,react):
    res = {}
    for name,seq,brack in dbn:
        re = react[name]
        if len(re) == len(seq) == len(brack):
            res[name]= (re,seq,brack)
        else:
            print "data for '%s' is corrupted, ignoring..." % name
    return res

def get_all_data(react, dbn):
    dbn = read_dbn(dbn)
    react = read_react(react)
    return combine_dbn_react(dbn,react)






#######
# generate data and learn model
########

import eden_rna
import eden.graph as eg
from scipy.sparse import vstack
from sklearn.linear_model import SGDRegressor
import numpy as np

from sklearn.ensemble import RandomForestRegressor as regressor
def mask(x,y):
    mask = np.array([ i for i,e in enumerate(y) if e!=-999.0])
    y=y[mask]
    x=x[mask]
    return x,y

def make_model(data,sequence_names=[], DEBUG=False,r=0,d=2):
    graphs =  [ eden_rna.sequence_dotbracket_to_graph(*data[key][1:]) for key in sequence_names]
    x = vstack( eg.vertex_vectorize(graphs,r=r,d=d) )

    if DEBUG:
        print "x matrix: ", x.shape
        print "graphs", len(graphs),
        nodecount = [len(g) for g in graphs]
        print nodecount, "sum", sum(nodecount)

    y = [f for key in sequence_names for f in data[key][0]]
    if DEBUG:
        print "found this many y values:", len(y)

    # filter x and y
    y=np.array(y)
    x,y= mask(x,y)
    if DEBUG:
        print "x,y after filtering",x.shape, y.shape
    model=regressor()
    model.fit(x,y)
    return model







##############
# PREDICT
#############
from graphlearn01.utils import draw as draw

def predict2(model,seq,stru):
    graph = eden_rna.sequence_dotbracket_to_graph(seq,stru)
    return model.predict(eg.vertex_vectorize([graph])[0])

def predict(model,graph):
    #graph = eden_rna.sequence_dotbracket_to_graph(seq,stru)
    return model.predict(eg.vertex_vectorize([graph])[0])




def dump_shape(result, fname):
    with open(fname,'w') as f:
        for k,v in result.items():
            vout = lambda x: "\n".join( [str(i + 1) + "\t" + str(e) for i, e in enumerate(v)])
            f.write(">%s\n%s\n\n" % (k,vout(v)))






##########
# OPTIMIZE
##########
def remove(li, it):
    li2 = list(li)
    li2.remove(it)
    return li2


from scipy.stats import spearmanr as corr
def calc(names,data, item,r,d):
    model = make_model(data,names,False,r,d)
    graph = eden_rna.sequence_dotbracket_to_graph(data[item][1],data[item][2])
    res = np.array(predict(model,graph))
    other = np.array(data[item][0])



    res,other = mask(res,other)
    value =  corr(res,other)[0]
    print '\t',len(data[item][1]),"\t", value
    return value

def optimize(data):
    for r in range(0,5):
        for d in range(0,5):
            # data is now  a dict name -> (react,sequence,dotbacket)
            names= data.keys()
            res= [ calc( remove(names,item), data , item,r,d) for item in names ]
            mederror= np.array(res).mean()
            print "r=%d d=%d res=%.2f\n\n" % (r,d, mederror)





#####
# ARGPARSE
#####

if __name__=='__main__':

    parser= get_argparser()
    args = parser.parse_args()
    DEBUG = True
    if DEBUG:
        print 'argparse args: ', args

    dbn = read_dbn(args.dbn)
    react = read_react(args.react)
    data= combine_dbn_react(dbn,react)
    # data is now  a dict name -> (react,sequence,dotbacket)
    model=make_model(data,data.keys(), DEBUG)
    targets ={a:[b,c] for (a,b,c) in read_dbn(args.target)}
    result = {}
    dump_shape(result,args.output)
    for target in targets:
        result[target] = predict2(model,*targets[target])
    optimize(data)
