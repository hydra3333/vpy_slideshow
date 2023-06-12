def encode_using_vsipe_ffmpeg(individual_chunk_id):
	# encode an individual chunk using vspipe and ffmpeg
	# 
	# using ChatGPT suggested method for non-blocking reads of subprocess stderr, stdout
	global SETTINGS_DICT
	global ALL_CHUNKS
	global ALL_CHUNKS_COUNT
	global ALL_CHUNKS_COUNT_OF_FILES
	
	def enqueue_output(out, queue):
		# for subprocess thread output queueing
		for line in iter(out.readline, b''):
			queue.put(line)
		out.close()

	FFMPEG_COMMAND = SETTINGS_DICT['FFMPEG_PATH']
	VSPIPE_COMMAND = SETTINGS_DICT['VSPIPE_PATH']

	try:
		# Define the commandlines for the subprocesses subprocesses
		
		# Run the commands in subprocesses
		process1 = subprocess.Popen(['vspipe.exe', '-p', '1', '-p', '1', '-'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		process2 = subprocess.Popen(['ffmpeg', '-i', 'pipe', 'etc'], stdin=process1.stdout, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

		# Create queues to store the output and error streams
		stderr_queue1 = Queue()
		stdout_queue2 = Queue()
		stderr_queue2 = Queue()

		# Launch separate threads to read the output and error streams
		stderr_thread1 = Thread(target=enqueue_output, args=(process1.stderr, stderr_queue1))
		stdout_thread2 = Thread(target=enqueue_output, args=(process2.stdout, stdout_queue2))
		stderr_thread2 = Thread(target=enqueue_output, args=(process2.stderr, stderr_queue2))
		stderr_thread1.daemon = True
		stdout_thread2.daemon = True
		stderr_thread2.daemon = True
		stderr_thread1.start()
		stdout_thread2.start()
		stderr_thread2.start()

		# Read output and error streams
		while True:
			try:
				stderr_line1 = stderr_queue1.get_nowait().decode('utf-8').strip()
				if stderr_line1:
					print(f"vspipe: {stderr_line1}")
				pass
			except Empty:
				pass
			try:
				stdout_line2 = stdout_queue2.get_nowait().decode('utf-8').strip()
				if stdout_line2:
					print(f"ffmpeg: {stdout_line2}")
				pass
			except Empty:
				pass
			try:
				stderr_line2 = stderr_queue2.get_nowait().decode('utf-8').strip()
				if stderr_line2:
					print(f"ffmpeg: {stderr_line2}")
				pass
			except Empty:
				pass
			if 	(not stderr_thread1.is_alive()) and
				(not stdout_thread2.is_alive()) and
				(not stderr_thread2.is_alive()) and 
				(stderr_queue1.empty()) and
				(stdout_queue2.empty()) and 
				(stderr_queue2.empty()):
					break
			# Introduce a 50ms delay to reduce CPU load
			time.sleep(0.05)  # Sleep for 50 milliseconds so as to not thrash the cpu
		#end while

		# Retrieve the remaining output and error streams
		output, error2 = process2.communicate()
		error1 = process1.stderr.read()

		# Decode any ffmpeg final output from bytes to string and print it
		print(f"ffmpeg: {output.decode('utf-8').strip()}")

		# Print any final error messages
		if error1:
				print(f"vspipe: {error1.decode('utf-8').strip()}")
		if error2:
				print(f"ffmpeg:: {error2.decode('utf-8').strip()}")
	except KeyboardInterrupt:
		# Retrieve the process IDs
		pid1 = process1.pid
		pid2 = process2.pid
		# Perform cleanup or other actions
		# before terminating the program
		process1.terminate()
		process2.terminate()
		process1.wait()
		process2.wait()
		# Delay before terminating forcefully with taskkill
		time.sleep(2)  # Add a delay of a couple of seconds
		# Terminate subprocesses forcefully using taskkill if they arem
		os.system(f'taskkill /F /PID {process1.pid}')
		os.system(f'taskkill /F /PID {process2.pid}')
		# Raise the exception again
		raise
	return