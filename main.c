// C implementation for testing only

#include <stdlib.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>
 
struct istwerte{
   float  upv_ist;
   float  upv_soll;
};

get_istwerte(int *tty_fd, struct istwerte *istwerte) {
	unsigned char c;
	while (c!='\n') {
		if (read(tty_fd,&c,1)>0) { 
			if (c=='\r') printf ("\n");
			printf("%c", c);
		}
	}
}

int main(int argc,char** argv)
{
        struct termios tio;
		struct istwerte istwerte;
        int tty_fd;
 
        unsigned char c;
 
        printf("Please start with %s /dev/ttyS1 (for example)\n",argv[0]);
  
        memset(&tio,0,sizeof(tio));
        tio.c_iflag=0;
        tio.c_oflag &= ~OPOST;					// raw mode
        tio.c_cflag=CS8|CREAD|CLOCAL;           // 8n1, see termios.h for more information
        tio.c_lflag=0;
        tio.c_cc[VMIN]=1;
        tio.c_cc[VTIME]=5;
 
        //tty_fd=open(argv[1], O_RDWR | O_NONBLOCK);      
		tty_fd=open(argv[1], O_RDWR);      
        cfsetospeed(&tio,9600); 
        cfsetispeed(&tio,9600); 
 
        tcsetattr(tty_fd,TCSANOW,&tio);
        
		int i=0;
		write(tty_fd,"\r",1);
		read(tty_fd,&c,1);
		while (i < 3) {
			write(tty_fd,"I",1);
			read(tty_fd,&c,1);
			write(tty_fd,"\r",1);
			read(tty_fd,&c,1);
			i++;
		}

		//while (c!='q')
        //{
        //        if (read(tty_fd,&c,1)>0)        write(STDOUT_FILENO,&c,1);              // if new data is available on the serial port, print it out
        //}
 
        close(tty_fd);
}
