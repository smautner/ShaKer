import numpy as np
from scipy.sparse import vstack
import eden
import eden_rna
from sklearn.ensemble import RandomForestRegressor
import simushape
import rna_tools

from sklearn.preprocessing import normalize




def crosspredict(data, keys, cutoff=0.01):
    # {seqname:[shapearray, sequence, structure]}

    for key in data.keys():
        trainkeys = remove(keys, key)
        mod = make_model(data,trainkeys)
        yield predict(mod, data[key][1], cutoff=cutoff)



def remove(li, it):
    li2 = list(li)
    li2.remove(it)
    return li2

def make_model( data,
                sequence_names=[],
                model=RandomForestRegressor(**{'oob_score': False,
                                             'min_impurity_split': 0.01,
                                             'bootstrap': True,
                                             'min_samples_leaf': 1,
                                             'n_estimators': 16,
                                             'min_samples_split': 6,
                                             'min_weight_fraction_leaf': 0.02,
                                             'max_features': None})):
    x,y = getXY(data,sequence_names)
    model.fit(x,y)
    return model





def getXY(data,keys):
    # data is  name -> (react,sequence,dotbacket)
    # we first make some graphs
    react,sequence,stru = zip(*[ data[k] for k in keys ])
    graphs  = map( getgraph, sequence,stru)

    # then we edenize
    x = vstack( eden.graph.vertex_vectorize(graphs,r=3,d=3))
    y= [y for reactlist in react for y in reactlist]
    y= np.array(y)
    # then done
    #print x,y
    return simushape.mask(x,y)


def getgraph(sequence,structure):
    return eden_rna.sequence_dotbracket_to_graph(sequence,structure)



def weighted_average(weights, react_arrays):

    '''
    t = [np.array(range(3)) for i in range(3)]
    g = [.5] * 3
    d = [t*g for t , g in zip(t,g)]
    print d
    print sum(d)
    '''

    weights = normalize(weights, norm='l1').tolist()[0]
    return sum([ array*weight for array, weight in zip(react_arrays,weights) ])

def predict(model, sequence, cutoff=0.0001):
    struct_proba = rna_tools.get_struct_and_proba(sequence,cutoff=cutoff)
    structures, weights =  zip(*struct_proba)
    print weights
    graphs = map(lambda x: getgraph(sequence,x), structures)
    vecs = list(eden.graph.vertex_vectorize(graphs,r=3,d=3))
    predictions_all_structures = [ model.predict(blob) for blob in vecs ]
    #res = np.vstack(res)
    return weighted_average(weights, predictions_all_structures)



