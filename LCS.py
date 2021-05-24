import numpy as np

# assume input_A is the theme
def lcs(input_A,input_B,equal_func,distance_threshold,input_A_ticks_per_beat,input_B_ticks_per_beat,verbose = False):
    # define table
    dp_tbl = np.zeros((len(input_A)+1,len(input_B)+1,4))
    dp_tbl = dp_tbl.astype('int32')
    # 0 for accumulated matched notes
    # 1 for direction
    # 2 for last referenced A id
    # 3 for last referenced B id

    # initialize
    dp_tbl[0,:,2] = np.ones((dp_tbl.shape[1])) * -1
    dp_tbl[:,0,2] = np.ones((dp_tbl.shape[0])) * -1

    for i in range(len(input_A)):
        for j in range(len(input_B)):
            
            # w is the matched note count in a group
            w = equal_func(input_A[i],input_B[j])
            if verbose:
                if max(i,j) <= 8:
                    print("Checking ({},{}) w={}".format(i,j,w))
                    print(input_A[i])
                    print(input_B[j])
            if w > 0:
                # There is a match
                # check the distance to last matched group
                if dp_tbl[i,j,3] == -1 and dp_tbl[i,j,2] == -1:
                    dp_tbl[i+1,j+1,0] = w
                    dp_tbl[i+1,j+1,1] = 0
                    dp_tbl[i+1,j+1,2] = i
                    dp_tbl[i+1,j+1,3] = j
                else:
                    _a = (input_B[j]["start"] - input_B[dp_tbl[i,j,3]]["start"]) / input_B_ticks_per_beat
                    _b = (input_A[i]["start"] - input_A[dp_tbl[i,j,2]]["start"]) / input_A_ticks_per_beat
                    if not i == dp_tbl[i,j,2] + 1:
                        # strictly adjcent in motif
                        dp_tbl[i+1,j+1,0] = w
                        dp_tbl[i+1,j+1,1] = 0
                        dp_tbl[i+1,j+1,2] = i
                        dp_tbl[i+1,j+1,3] = j
                    else:
                        r =  abs(_a - _b)
                        if  r > distance_threshold:
                            dp_tbl[i+1,j+1,0] = w
                            dp_tbl[i+1,j+1,1] = 0
                            dp_tbl[i+1,j+1,2] = i
                            dp_tbl[i+1,j+1,3] = j
                        else:
                            dp_tbl[i+1,j+1,0] = dp_tbl[i,j,0] + w
                            dp_tbl[i+1,j+1,1] = 3
                            dp_tbl[i+1,j+1,2] = i
                            dp_tbl[i+1,j+1,3] = j
            else:
                # No match
                if dp_tbl[i,j+1,0] > dp_tbl[i+1,j,0]: 
                    # from up
                    dp_tbl[i+1,j+1,0] = dp_tbl[i,j+1,0]
                    dp_tbl[i+1,j+1,1] = 1
                    dp_tbl[i+1,j+1,2] = dp_tbl[i,j+1,2]
                    dp_tbl[i+1,j+1,3] = dp_tbl[i,j+1,3]
                elif dp_tbl[i,j+1,0] < dp_tbl[i+1,j,0]:
                    # from left
                    dp_tbl[i+1,j+1,0] = dp_tbl[i+1,j,0]
                    dp_tbl[i+1,j+1,1] = 2
                    dp_tbl[i+1,j+1,2] = dp_tbl[i+1,j,2]
                    dp_tbl[i+1,j+1,3] = dp_tbl[i+1,j,3]
                else:
                    if dp_tbl[i,j+1,1] == 3:
                        # from up
                        dp_tbl[i+1,j+1,0] = dp_tbl[i,j+1,0]
                        dp_tbl[i+1,j+1,1] = 1
                        dp_tbl[i+1,j+1,2] = dp_tbl[i,j+1,2]
                        dp_tbl[i+1,j+1,3] = dp_tbl[i,j+1,3]
                    else:
                        # from left
                        dp_tbl[i+1,j+1,0] = dp_tbl[i+1,j,0]
                        dp_tbl[i+1,j+1,1] = 2
                        dp_tbl[i+1,j+1,2] = dp_tbl[i+1,j,2]
                        dp_tbl[i+1,j+1,3] = dp_tbl[i+1,j,3]
    
    # backtrace
    match_pattern = []
    match_idx_A = []
    match_idx_B = []

    
    # Find index of maximum value from 2D numpy array
    max_result = np.where(dp_tbl[:,:,0] == np.amax(dp_tbl[:,:,0]))
    
    listOfCordinates = list(zip(max_result[0], max_result[1]))
        

    c_i = listOfCordinates[0][0]
    c_j = listOfCordinates[0][1]

    while(not dp_tbl[c_i,c_j,1] == 0):
        if dp_tbl[c_i,c_j,1] == 3:
            match_pattern.append(input_A[c_i-1])
            match_idx_A.append(c_i-1)
            match_idx_B.append(c_j-1)
            c_i -= 1
            c_j -= 1
        elif dp_tbl[c_i,c_j,1] == 2:
            c_j -= 1
        else:
            c_i -= 1
    
    if  not (c_i == 0 or c_j == 0):
        # start from middle
        match_idx_A.append(c_i-1)
        match_idx_B.append(c_j-1)
    
    match_pattern.reverse()
    match_idx_A.reverse()
    match_idx_B.reverse()


    c_i = listOfCordinates[0][0]
    c_j = listOfCordinates[0][1]

    


    if verbose:
        print("input_A seq : {}".format(input_A))
        print("input_B seq : {}".format(input_B))
        print("len input A : {}".format(len(input_A)))
        print("len input B : {}".format(len(input_B)))
        # print("Matched seq : {}".format(match_pattern))
        print("Total match length : {}".format(int(dp_tbl[c_i,c_j,0])))
        print("Matched seq idx in A: {}".format(match_idx_A))
        print("Matched seq idx in B: {}".format(match_idx_B))

    return match_idx_A , match_idx_B , int(dp_tbl[c_i,c_j,0])