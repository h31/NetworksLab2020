#pragma once

#ifndef _SSIZE_T_DEFINED
    #ifdef _WIN64
        typedef unsigned __int64 ssize_t;
    #else
        typedef _W64 unsigned int ssize_t;
    #endif
#define _SSIZE_T_DEFINED
#endif

#define bzero(b,len) (memset((b), '\0', (len)), (void) 0)  