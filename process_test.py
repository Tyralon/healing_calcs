import multiprocessing
import random
import time
from multiprocessing import Process, Lock, Value, Array, Manager, Pool
from functools import partial

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

def foo_async(numbers, value, limit):
	for _ in range(limit):
		val = foo(value)
		numbers.append(val)
	
	return numbers

def callback_fn(result, numbers):
	numbers[:] = result

if __name__ == '__main__':

	mngr = Manager()
	numbers = mngr.list([])
	counter = mngr.Value('i', 0)
	numbers2 = []
	counter2 = mngr.Value('i', 0)
	lock = mngr.Lock()

	arg = (lock, counter, numbers, 9, 7,)
	arg2 = (lock, counter2, numbers2, 9, 3,)

#	foo_proc(lock, counter, numbers, 9, 7,)

	with Pool(9) as pool:
		pool.apply_async(time.sleep, [5])
		pool.apply_async(foo_async, args=(numbers2, 9, 3,), callback=partial(callback_fn, numbers=numbers2))
		pool.apply(foo_proc, arg)
#		pool.starmap(foo_proc, [arg, arg])

#	numbers.clear()
#	counter.value = 0

#		pool.starmap(foo_proc, [arg2, arg2])

#		numbers2 = result.get()
		pool.close()
		pool.join()

		print(numbers[:])
		print(counter.value)

		print(numbers2[:])
		print(counter2.value)

#	counter = 0
#	numbers = []

#	print(numbers)
#	print(counter)
