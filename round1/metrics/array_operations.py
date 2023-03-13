import time
import numpy as np

l = [1500 for _ in range(10000)]
ll = [50 for _ in range(10000)]


# Python
st = time.time()

print(sum([i * j for i, j in zip(l, ll)]) / sum(ll))

# price_volume_sum = 0
# volume_sum = 0
# for i in range(len(l)):
#     price_volume_sum += l[i] * ll[i]
#     volume_sum += ll[i]

# print(price_volume_sum / volume_sum)


et = time.time()
elapsed_time1 = et - st


# Numpy + conversion
st = time.time()

l = np.array(l)
ll = np.array(ll)

print((l * ll).sum() / ll.sum())

et = time.time()
elapsed_time2 = et - st


print("Elapsed using python:", elapsed_time1)
print("Elapsed using numpy:", elapsed_time2)
