
"""This module calls the multi-echelon supply chain simulation
as a black box function to optimize inventory policy
"""

__author__ = 'Anshul Agarwal'


#from simulation.simLostSales import simulate_network
from simulation.simBackorder import simulate_network
import numpy as np
import rbfopt
import csv


# Read the historical demand data
demandAllNodes = []
with open('data/demandData.csv', 'r') as f:
    next(f)  # skip headings
    reader = csv.reader(f)
    for a in reader:
        demandAllNodes.append([float(j) for j in a])

demandAllNodes = np.array(demandAllNodes)  # contains all nodes except the source node

# Read the historical data on lead time delay
leadTimeDelay = []
with open('data/leadTimeExtraDays.csv', 'r') as f:
    reader = csv.reader(f)
    for a in reader:
        leadTimeDelay.append(int(a[0]))

leadTimeDelay = np.array(leadTimeDelay)

# Define the supply chain network
numNodes = 6
nodeNetwork = np.zeros((numNodes, numNodes))
nodeNetwork[0, 1] = 1
nodeNetwork[1, 2] = 1
nodeNetwork[1, 3] = 1
nodeNetwork[3, 4] = 1
nodeNetwork[3, 5] = 1

# Initialize network nodes
defaultLeadTime = np.array([0, 3, 4, 4, 2, 2])
serviceTarget = np.array([0.0, 0.95, 0.95, 0.0, 0.95, 0.95])


# function to evaluate the objective function for optimization
# we minimize on-hand inventory and heavily penalize not meeting
# the beta service level (demand volume based)

def getObj(initial_guess):
    
    # Split the initial guess to get base stock and ROP
    base_stock_guess = initial_guess[:(numNodes - 1)]
    ROP_guess = initial_guess[(numNodes - 1):]
    
    # Insert the supply node's base stock
    baseStock = np.insert(base_stock_guess, 0, 10000)
    
    # Insert a zero ROP for the first source node
    ROP = np.insert(ROP_guess, 0, 0)
    
    # Initialize inventory level
    initialInv = 0.9*baseStock
    
    replications = 20
    totServiceLevel = np.zeros(numNodes)
    totAvgOnHand = 0.0
    for i in range(replications):
        nodes = simulate_network(i,numNodes,nodeNetwork,initialInv,ROP,baseStock,
                                 demandAllNodes,defaultLeadTime,leadTimeDelay)
    	
        totServiceLevel = np.array([totServiceLevel[j] + 
                                    nodes[j].serviceLevel for j in range(len(nodes))]) #convert list to array
    	
        totAvgOnHand += np.sum([nodes[j].avgOnHand for j in range(len(nodes))])
    
    servLevelPenalty = np.maximum(0, serviceTarget - totServiceLevel/replications) # element-wise max
    objFunValue = totAvgOnHand/replications + 1.0e6*np.sum(servLevelPenalty)
    return objFunValue


######## Main statements to call optimization ########

base_stock_initial_guess = [3000, 600, 900, 300, 600]
ROP_initial_guess = [1000, 250, 200, 150, 200]
guess = base_stock_initial_guess + ROP_initial_guess # concatenate lists
numVars = len(guess)

settings = rbfopt.RbfoptSettings(max_evaluations=500,
								minlp_solver_path="C:/Anaconda3/rbfopt_solvers/bonmin-win64/bonmin.exe",
								nlp_solver_path="C:/Anaconda3/rbfopt_solvers/ipopt-win64/ipopt.exe")

bb = rbfopt.RbfoptUserBlackBox(numVars, np.array([0] * numVars), np.array(guess),
                               np.array(['R'] * numVars), getObj)
alg = rbfopt.RbfoptAlgorithm(settings, bb)
val, x, itercount, evalcount, fast_evalcount = alg.optimize()
print(val, x, itercount, evalcount, fast_evalcount)
