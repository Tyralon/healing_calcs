import threading
import random

counter = 0
numbers = []

def foo(value):
	return random.randint(0, value)

def foo_thread(lock, value, limit):
	global counter
	global numbers
	
	while True:
		lock.acquire()
		if counter >= limit:
			lock.release()
			break
		lock.release()
	
		val = foo(value)
		numbers.append(val)

		lock.acquire()
		counter += 1
		lock.release()


def main_task():
	global counter
	global numbers
	lock = threading.Lock()

	t1 = threading.Thread(target=foo_thread, args=(lock, 9, 7,))
	t2 = threading.Thread(target=foo_thread, args=(lock, 9, 7,))

	t1.start()
	t2.start()

	t1.join()
	t2.join()

	print(numbers)
	print(counter)

	counter = 0
	numbers = []

	print(numbers)
	print(counter)

main_task()
