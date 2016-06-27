from shared.ops import *
from shared.util import *

#hc_tf.config.optimizer(["adam"], lr=[1e-3,1e-5])
#hc_tf.config.deconv
#hc_tf.config.conv(filter=3, )
#hc_tf.config.reshape(method)

#hc_tf.build.optimizer()
#hc_tf.build.deconv
#hc_tf.build.conv
#hc_tf.build.reshape()

def build_reshape(output_size, nodes, method, batch_size):
    node_size = sum([int(x.get_shape()[1]) for x in nodes])
    dims = output_size-node_size
    if(method == 'noise'):
        noise = tf.random_uniform([batch_size, dims],-1, 1)
        result = tf.concat(1, nodes+[noise])
    elif(method == 'tiled'):
        t_nodes = tf.concat(1, nodes)
        dims =  int(t_nodes.get_shape()[1])
        result= tf.tile(t_nodes,[1, output_size//dims])
        print("TILED", t_nodes, result, output_size//dims, output_size, dims)
        width = output_size - int(result.get_shape()[1])
        if(width > 0):
            print("WIDTH is ", width)
            #zeros = tf.zeros([batch_size, width])
            slice = tf.slice(result, [0,0],[batch_size,width])
            result = tf.concat(1, [result, slice])


    elif(method == 'zeros'):
        result = tf.concat(1, nodes)
        result = tf.pad(result, [[0, 0],[dims//2, dims//2]])
        width = output_size - int(result.get_shape()[1])
        if(width > 0):
            zeros = tf.zeros([batch_size, width])
            result = tf.concat(1, [result, zeros])
    elif(method == 'linear'):
        result = tf.concat(1, [y, z])
        result = linear(result, dims, 'g_input_proj')
    else:
        assert 1 == 0
    return result

def pad_input(primes, output_size, nodes):
    node_size = sum([int(x.get_shape()[1]) for x in nodes])
    dims = output_size
    prime = primes[0]*primes[1]
    while(dims-node_size < 0):
        dims += prime
    if(dims % (prime) != 0):
        dims += (prime-(dims % (prime)))
    return dims

def find_smallest_prime(x, y):
    for i in range(3,x-1):
        for j in range(3, y-1):
            if(x % (i) == 0 and y % (j) == 0 and x // i == y // j):
                return i,j
    return None,None

def build_conv_tower(result, layers, filter, batch_size, batch_norm_enabled, batch_norm_last_layer, name, activation):
    for i, layer in enumerate(layers):
        stride = 2
        if filter > result.get_shape()[2]:
            filter = int(result.get_shape()[2])
            stride = 1
        if filter > result.get_shape()[3]:
            filter = int(result.get_shape()[3])
            stride = 1
        result = conv2d(result, layer, name=name+str(i), k_w=filter, k_h=filter, d_h=stride, d_w=stride)
        if(len(layers) == i+1):
            if(batch_norm_last_layer):
                result = batch_norm(batch_size, name=name+'_bn_'+str(i))(result)
            print("Skipping last layer")
        else:
            print("Adding nonlinear")
            if(batch_norm_enabled):
                result = batch_norm(batch_size, name=name+'_bn_'+str(i))(result)
            result = activation(result)
    result = tf.reshape(result, [batch_size, -1])
    return result

def build_deconv_tower(result, layers, dims, conv_size, name, activation, batch_norm_enabled, batch_norm_last_layer, batch_size,last_layer_stddev):
    for i, layer in enumerate(layers):
        j=int(result.get_shape()[1])*2
        k=int(result.get_shape()[2])*2
        stride=2
        if(j > dims[0] or k > dims[1] ):
            j = dims[0]
            k = dims[1]
            stride=1

        output = [batch_size, j,k,int(layer)]
        stddev = 0.002
        if(len(layers) == i+1):
            if(batch_norm_last_layer):
                stddev = 0.15
        result = deconv2d(result, output, name=name+str(i), k_w=conv_size, k_h=conv_size, d_h=stride, d_w=stride, stddev=stddev)
        if(len(layers) == i+1):
            if(batch_norm_last_layer):
                result = batch_norm(batch_size, name=name+'_bn_'+str(i))(result)
        else:
            if(batch_norm_enabled):
                result = batch_norm(batch_size, name=name+'_bn_'+str(i))(result)
            result = activation(result)
    return result


def build_conv_config(layers, start, end):
    def get_layer(layer, i):
        reverse = 2**(layer+1)*i
        noise = int(np.random.uniform(-1,1)*10)*i
        print('--', 2**(layer+1), reverse, noise, reverse+noise)

        result = reverse
        if(result < 3): 
            result = 3
        if(reverse+noise > 3):
            result = reverse+noise
        return result
    def get_option(i):
        return [get_layer(layer, i) for layer in range(layers)]
    return [get_option(i) for i in np.arange(start, end)]


def build_deconv_config(layers,start, end):
    def get_layer(layer, i):
        reverse = 2**(layers-layer+1)*i
        noise = int(np.random.uniform(-1,1)*10)*i
        print('--', 2**(layer), reverse, noise, reverse+noise)

        result = reverse
        if(result < 3): 
            result = 3
        if(reverse+noise > 3):
            result = reverse+noise
        return result
    def get_option(i):
        return [get_layer(layer, i) for layer in range(layers)]
    return [get_option(i) for i in np.arange(start, end)]


def get_graph_vars(sess, graph):

    summary = get_tensor("hc_summary")
    all_vars = sess.run([s[3] for s in summary])
    i=0
    retv = {'weights':{}}
    for shape, name, dtype, _ in summary:
        data=all_vars[i]
        retv['weights'][name]={
                'shape':[int(s) for s in shape],
                'name':name,
                'dtype':str(dtype),
                'value':str(data)
                }
        i+=1
        
    return retv
