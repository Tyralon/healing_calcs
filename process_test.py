import multiprocessing
import random
from multiprocessing import Process, Lock, Value, Array, Manager

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

	p1 = Process(target=foo_proc, args=(lock, counter, numbers, 9, 7,))
	p2 = Process(target=foo_proc, args=(lock, counter, numbers, 9, 7,))

	p1.start()
	p2.start()

	p1.join()
	p2.join()

	print(numbers[:])
	print(counter.value)

#	counter = 0
#	numbers = []

#	print(numbers)
#	print(counter)
