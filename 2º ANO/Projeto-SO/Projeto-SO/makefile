CC = gcc
FLAGS = -Wall -Wextra -pthread
LIBS = -lcrypto -lssl

controller: controller.o miner.o PoW.o statistics.o validator.o
	$(CC) $(FLAGS) -o controller controller.o miner.o PoW.o statistics.o validator.o $(LIBS)

controller.o: controller.c controller.h 
	$(CC) $(FLAGS) -c controller.c

miner.o: miner.c miner.h
	$(CC) $(FLAGS) -c miner.c

PoW.o: PoW.c PoW.h
	$(CC) $(FLAGS) -c PoW.c

statistics.o: statistics.c controller.h
	$(CC) $(FLAGS) -c statistics.c

validator.o: validator.c controller.h
	$(CC) $(FLAGS) -c validator.c

TXgen: TXgen.o
	$(CC) $(FLAGS) -o TXgen TXgen.o

TXgen.o: TXgen.c controller.h
	$(CC) $(FLAGS) -c TXgen.c

clear:
	rm -f miner.o controller.o TXgen.o statistics.o PoW.o validator.o controller TXgen

clean: clear
	rm DEIChain_log.txt
