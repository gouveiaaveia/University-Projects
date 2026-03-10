CC = gcc
FLAGS = -Wall -Wextra -pthread

cliente: cliente.o 
	$(CC) $(FLAGS) -o cliente cliente.o

cliente.o: cliente.c config.h
	$(CC) $(FLAGS) -c cliente.c

servidor: servidor.o 
	$(CC) $(FLAGS) -o servidor servidor.o

servidor.o: servidor.c config.h
	$(CC) $(FLAGS) -c servidor.c

clear:
	rm -f *.o cliente servidor