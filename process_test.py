import multiprocessing
import random
from multiprocessing import Process, Lock, Value, Array, Manager, Pool

counter = 0
numbers = []

def foo(value):
	return random.randint(0, value)

def foo_proc(lock, counter, numbers, value, limit):

	while True:
		lock.acquire()
		if counter.value >= limit:
			lock.release()
			break
		else:
			counter.value += 1
			lock.release()

		val = foo(value)
		numbers.append(val)



if __name__ == '__main__':

	mngr = Manager()
	numbers = mngr.list([])
	counter = mngr.Value('i', 0)
	lock = mngr.Lock()

	arg = (lock, counter, numbers, 9, 7,)

	with Pool(2) as pool:
		pool.starmap(foo_proc, [arg, arg])

	pool.close()
	pool.join()

	print(numbers[:])
	print(counter.value)

#	counter = 0
#	numbers = []

#	print(numbers)
#	print(counter)
