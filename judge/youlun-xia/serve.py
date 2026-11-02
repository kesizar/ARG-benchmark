"""Serve only the player directory with byte ranges required for MP4 seeking."""
import argparse,pathlib,re,functools
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
class Handler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
    def list_directory(self,path):self.send_error(404);return None
    def send_head(self):
        self.byte_range=None
        path=pathlib.Path(self.translate_path(self.path))
        value=self.headers.get('Range')
        if not value or not path.is_file():return super().send_head()
        size=path.stat().st_size;match=re.fullmatch(r'bytes=(\d+)-(\d*)',value)
        if not match:self.send_error(416);return None
        start=int(match[1]);end=min(int(match[2]) if match[2] else size-1,size-1)
        if start>=size or end<start:self.send_error(416);return None
        stream=path.open('rb');stream.seek(start);self.byte_range=end-start+1
        self.send_response(206);self.send_header('Content-Type',self.guess_type(str(path)));self.send_header('Accept-Ranges','bytes');self.send_header('Content-Range',f'bytes {start}-{end}/{size}');self.send_header('Content-Length',str(self.byte_range));self.end_headers();return stream
    def copyfile(self,source,output):
        if self.byte_range is None:return super().copyfile(source,output)
        remaining=self.byte_range
        while remaining:
            block=source.read(min(65536,remaining))
            if not block:break
            try:output.write(block)
            except (ConnectionResetError,BrokenPipeError,ConnectionAbortedError):break
            remaining-=len(block)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8821);args=parser.parse_args()
    root=pathlib.Path(__file__).resolve().parents[2]/'tasks/youlun-xia'
    ThreadingHTTPServer(('127.0.0.1',args.port),functools.partial(Handler,directory=str(root))).serve_forever()
