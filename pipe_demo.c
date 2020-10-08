/** Pipeline between three processes. http://stackoverflow.com/q/20056084/
 */
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <sys/types.h> /* pid_t */
#include <unistd.h>

#define PROGNAME "pipeline-three-processes"

#define Close(FD) do {                                  \
    int Close_fd = (FD);                                \
    if (close(Close_fd) == -1) {                        \
      perror("close");                                  \
      fprintf(stderr, "%s:%d: close(" #FD ") %d\n",     \
                __FILE__, __LINE__, Close_fd);          \
    }                                                   \
}while(0)

static void
report_error_and_exit_helper(const char* message, void (*exit_func)(int)) {
    fprintf(stderr, "%s: error: %s (system: %s)\n",
            PROGNAME, message ? message : "", strerror(errno));
    exit_func(EXIT_FAILURE);
}

static void report_error_and_exit(const char* message) {
    report_error_and_exit_helper(message, exit);
}

static void _report_error_and_exit(const char* message) {
    report_error_and_exit_helper(message, _exit);
}


/* move oldfd to newfd */
static void redirect(int oldfd, int newfd) {
    if (oldfd != newfd) {
        if (dup2(oldfd, newfd) != -1)
            Close(oldfd); /* successfully redirected */
        else
            _report_error_and_exit("dup2");
    }
}

static void run(char* const argv[], int in, int out) {
    redirect(in, STDIN_FILENO);     /* <&in    : child reads from in */
    redirect(out, STDOUT_FILENO); /* >&out : child writes to out */

    execvp(argv[0], argv);
    _report_error_and_exit("execvp");
}

int main(void) {
    const char *ls[] = { "ls", "-l", NULL };
    const char *sort[] = { "sort", "-k9", NULL };
    const char *less[] = { "less", NULL };
    const char** command[] = { ls, sort, less };
    int n = sizeof(command) / sizeof(*command);

    /* run all commands but the last */
    int i = 0, in = STDIN_FILENO; /* the first command reads from stdin */
    for ( ; i < (n-1); ++i) {
        int fd[2]; /* in/out pipe ends */
        pid_t pid; /* child's pid */

        if (pipe(fd) == -1)
            report_error_and_exit("pipe");
        else if ((pid = fork()) == -1)
            report_error_and_exit("fork");
        else if (pid == 0) { /* run command[i] in the child process */
            Close(fd[0]); /* close unused read end of the pipe */
            run((char * const*)command[i], in, fd[1]); /* $ command < in > fd[1] */
        }
        else { /* parent */
            assert (pid > 0);
            Close(fd[1]); /* close unused write end of the pipe */
            Close(in);        /* close unused read end of the previous pipe */
            in = fd[0]; /* the next command reads from here */
        }
    }
    /* run the last command */
    run((char * const*)command[i], in, STDOUT_FILENO); /* $ command < in */
}