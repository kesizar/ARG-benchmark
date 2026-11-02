"""Match the official GitHub Pages UTF-8 Content-Type; forum's meta contains a non-ASCII hyphen."""
from serve_static import QuietHandler,main
original=QuietHandler.guess_type
def guess_type(self,path):
 value=original(self,path)
 return value+'; charset=utf-8' if value.startswith('text/') else value
QuietHandler.guess_type=guess_type
if __name__=='__main__':main()
