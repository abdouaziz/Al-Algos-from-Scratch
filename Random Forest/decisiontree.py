import numpy as np 


class DecisionTreeClassifier():
	"""
	Decision Tree Classifier
	
	Parameters
	----------
	max_depth : integer (Default 'inf'), maximum depth allowed in the decision tree
	
	min_samples_split : integer (Default 2), minimum nodes to consider before splitting
	
	n_classes : integer (Default None), if None find out from training dataset labels
	
	Attributes
	----------
	tree_ : dict, dictionary representation of tree
	
	depth_ : integer, current maximum depth of tree
	
	"""
	def __init__(self, max_depth=None, min_samples_split=2, n_classes=None):
		self.__root = None
		self.__max_depth = float('inf') if max_depth==None else max_depth
		self.__min_samples_split = min_samples_split
		self.__n_classes = n_classes
		self.__depth = 0

	def __gini_index(self,groups, y):
		n_instances = len(groups[0])+len(groups[1])  # count of all samples
		gini = 0.0 # sum weighted Gini index for each group
		for indexes in groups:
			size = len(indexes)
			if size == 0: continue # avoid divide by zero
			score = 0.0
			# score the group based on the score for each class
			for class_val in np.unique(y):
				p = (y[indexes]==class_val).sum()/size 
				score += p*p
			# weight the group score by its relative size
			gini +=  (1-score) * (size / n_instances)
		return gini

	def __get_split(self,X,y):
		b_index, b_value, b_score, b_groups = float('inf'), float('inf'), float('inf'), None
		for col_ind in range(X.shape[1]): #for each features
			for val in np.unique(X[:,col_ind]): #for each unique value of that feature

				#left_index indexes lower than val for feature, right_index indexes greater that val for feature
				left_index = np.reshape( np.argwhere(X[:,col_ind]<val) ,(-1,))
				right_index = np.reshape( np.argwhere(X[:,col_ind]>=val) ,(-1,))

				#find gini index
				gini = self.__gini_index((left_index,right_index), y)

				if gini < b_score:
					b_index, b_value, b_score, b_groups = col_ind, val, gini, (left_index, right_index)

		return {'index':b_index, 'value':b_value, 'groups':b_groups}

	def __to_terminal(self,classes):
		# Create a terminal node value
		cls,cnt = np.unique(classes,return_counts=True)
		probs = np.zeros(self.__n_classes)
		for cl,cn in zip(cls,cnt): probs[int(cl)]= cn/sum(cnt)
		return cls[np.argmax(cnt)], probs

	def __split(self, node, X, y, depth):
		self.__depth = max(depth, self.__depth)
		left, right = node.pop('groups')
		# check for a no split
		if len(left)==0 or len(right)==0:
			node['left'] = node['right'] = self.__to_terminal(y[np.append(left,right)])
			return

		# check for max depth
		if depth >= self.__max_depth:
			node['left'], node['right'] = self.__to_terminal(y[left]), self.__to_terminal(y[right])
			return

		# process left child
		if len(left) <= self.__min_samples_split:
			node['left'] = self.__to_terminal(y[left])
		else:
			node['left'] = self.__get_split(X[left],y[left])
			self.__split(node['left'], X[left], y[left], depth+1)
		# process right child
		if len(right) <= self.__min_samples_split:
			node['right'] = self.__to_terminal(y[right])
		else:
			node['right'] = self.__get_split(X[right],y[right])
			self.__split(node['right'],X[right],y[right], depth+1)

	def fit(self,X,y):
		"""
		Fit X using y by optimizing splits costs using gini index
		
		Parameters
		----------
		X : 2D numpy array, independent variables
		
		y : 1D numpy array, dependent variable

		"""
		self.__n_classes = len(np.unique(y)) if self.__n_classes==None else self.__n_classes
		self.__root = self.__get_split(X,y)
		self.__split(self.__root, X, y, 1)

	def predict(self,rows):
		"""
		Predict dependent variable
		
		Parameters
		---------
		X : numpy array, independent variables
		
		Returns
		-------
		predicted labels    
		
		"""
		return np.array([ self.__predict_row(row,self.__root)[0] for row in rows ])

	def predict_proba(self,X):
		"""
		Predict probability of all classes
	
		Parameters
		----------
		X : numpy array, independent variables
	   
		Returns
		-------
		probability of each class [ n_samples, n_classes ]
		
		"""
		return np.array([ self.__predict_row(row,self.__root)[1] for row in X ])

	def __predict_row(self,row,node):
		if row[node['index']] < node['value']:
			if isinstance(node['left'], dict):  return self.__predict_row(row,node['left'])
			else: return node['left']
		else:
			if isinstance(node['right'], dict): return self.__predict_row(row,node['right'])
			else: return node['right']

	def score(self,X,y): 
		"""
		Calculate accuracy from independent variables
		
		Parameters
		----------
		X : numpy array, independent variables
		
		y : numpy array, dependent variable
		
		Returns
		-------
		accuracy score
		
		"""
		return (y==self.predict(X)).sum()/len(y)

	@property 
	def depth(self): return self.__depth

	@property 
	def tree_(self): return self.__root



class DecisionTreeRegressor():
	"""
	Decision Tree Regressor
	
	Parameters
	----------
	criterion : ('mse', 'mae', 'std') ( Default 'mse' )
		The function to measure the quality of a split.
		'mse' is mean squared error
		'mae' is mean absolute error
		'std' is standard deviation
   
	max_depth : integer (Default 'inf'), maximum depth allowed in the decision tree
	
	min_samples_split : integer (Default 2), minimum nodes to consider before splitting
	
	Attributes
	----------
	tree_ : dict, dictionary representation of tree
	
	depth_ : integer, current maximum depth of tree
	
	"""
	def __init__(self, criterion='mse', max_depth=None, min_samples_split=2):
		self.__root = None
		self.__cost = { 'mse':self.__mse,'std':self.__std,'mae':self.__mae }[criterion]
		self.__max_depth = float('inf') if max_depth==None else max_depth
		self.__min_samples_split = min_samples_split
		self.__depth = 0

	def __std(self,y):
		squared_error = (y-y.mean())**2
		return np.sqrt(  np.sum(squared_error)/len(y)  )

	def __mse(self,y):
		squared_error = (y-y.mean())**2
		return np.sum( squared_error/len(y) )

	def __mae(self,y): return np.sum(abs(y-y.mean())/len(y))

	def __computeCost(self,groups, y):
		n_instances = len(groups[0])+len(groups[1])  # count of all samples
		weighted_cost = 0.0 # sum weighted Gini index for each group
		for indexes in groups:
			size = len(indexes)
			# avoid divide by zero
			if size == 0: continue
			weighted_cost +=  self.__cost(y[indexes]) * (size/n_instances)
		return weighted_cost

	def __get_split(self,X,y):
		b_index, b_value, b_cost, b_groups = float('inf'), float('inf'), float('inf'), None
		for col_ind in range(X.shape[1]): #no of features
			for val in np.unique(X[:,col_ind]): #for each unique value in each of the features

				#left_index indexes lower than val for feature, right_index indexes greater that val for feature
				left_index = np.reshape( np.argwhere(X[:,col_ind]<val), (-1,) )
				right_index = np.reshape( np.argwhere(X[:,col_ind]>=val), (-1,) )

				#find gini index
				cost = self.__computeCost((left_index,right_index), y)
				if cost < b_cost:
					b_index, b_value, b_cost, b_groups = col_ind, val, cost, (left_index, right_index)
		return {'index':b_index, 'value':b_value, 'groups':b_groups}

	def __to_terminal(self,y): return y.mean()

	def __split(self,node, X, y,  depth):
		self.__depth = max(depth,self.__depth)
		left, right = node.pop('groups')

		# check for a no split
		if len(left)==0 or len(right)==0:
			node['left'] = node['right'] = self.__to_terminal(y[np.append(left,right)])
			return

		# check for max depth
		if depth >= self.__max_depth:
			node['left'], node['right'] = self.__to_terminal(y[left]), self.__to_terminal(y[right])
			return

		# process left child
		if len(left) <= self.__min_samples_split:
			node['left'] = self.__to_terminal(y[left])
		else:
			node['left'] = self.__get_split(X[left],y[left])
			self.__split(node['left'], X[left], y[left], depth+1)

		# process right child
		if len(right) <= self.__min_samples_split:
			node['right'] = self.__to_terminal(y[right])
		else:
			node['right'] = self.__get_split(X[right],y[right])
			self.__split(node['right'],X[right],y[right], depth+1)

	def fit(self, X, y):
		"""
		Fit X using y by optimizing splits costs using given criterion
		
		Parameters
		----------
		X : 2D numpy array, independent variables
		
		y : 1D numpy array, dependent variable
		
		"""
		self.__root = self.__get_split(X,y)
		self.__split(self.__root, X, y, 1)

	def __predict_row(self,row,node):
		if row[node['index']] < node['value']:
			if isinstance(node['left'], dict): return self.__predict_row(row,node['left'])
			else: return node['left']
		else:
			if isinstance(node['right'], dict): return self.__predict_row(row,node['right'])
			else: return node['right']

	def predict(self, X): 
		"""
		Predict dependent variable

		Parameters
		----------
		X : numpy array, independent variables
		
		Returns
		-------
		predicted values
		
		"""
		return np.array( [self.__predict_row(row,self.__root) for row in X] )

	def score(self,X,y):
		"""
		Computer Coefficient of Determination (rsquare)
		
		Parameters
		----------
		X : 2D numpy array, independent variables
	   
		y : numpy array, dependent variables
		
		Returns
		-------
		r2 values
		"""
		y_pred = self.predict(X)
		return 1-( np.sum( (y-y_pred)**2 )/np.sum( (y-y.mean())**2 ) )

	@property
	def depth_(self): return self.__depth

	@property
	def tree_(self): return self.__root