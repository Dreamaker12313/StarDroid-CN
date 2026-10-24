#include "StormLib.h"
#include <fstream>
#include <vector>
int main(int n,char**v){HANDLE a,f;if(!SFileOpenArchive(v[1],0,MPQ_OPEN_READ_ONLY,&a)||!SFileOpenFileEx(a,v[2],SFILE_OPEN_FROM_MPQ,&f))return 1;DWORD size=SFileGetFileSize(f,nullptr),read=0;std::vector<char>b(size);if(!SFileReadFile(f,b.data(),size,&read,nullptr)||read!=size)return 2;std::ofstream o(v[3],std::ios::binary);o.write(b.data(),size);SFileCloseFile(f);SFileCloseArchive(a);}
