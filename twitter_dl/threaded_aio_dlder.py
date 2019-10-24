import asyncio
import aiohttp
import threading
import logging
from queue import Queue, Empty

# threaded asyncio
def loop_in_thread(async_entry, *args, **kwargs):
    log = logging.getLogger('LoopThread')
    log.debug('loop begin...')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(async_entry(*args, **kwargs))
    loop.close()
    log.debug('loop end...')

class AioDownloader():
    def __init__(self):
        self.q = Queue()
        self.threads = []
        self.log = logging.getLogger('AioDlder')
    
    def start(self, num_threads, num_coros):
        for _ in range(num_threads):
            t = threading.Thread(target=loop_in_thread, 
                    args=(self.sched_downloaders, num_coros))
            self.threads.append(t)
            t.start()
    
    def join(self):
        self.add_endsignal()
        for t in self.threads:
            t.join()
    
    def add_endsignal(self):
        self.q.put((None, None))
    
    def add_url(self, url, dest):
        self.q.put((url, dest))

    async def downloader(self, session, url, dest, sem):
        try:
            #now = loop.time()
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    with open(dest, 'wb') as f:
                        f.write(data)
                    #self.log.info(f'{resp.url} ==> {dest}, {loop.time()-now:.2f}s used')
                    self.log.info(f'{resp.url} ==> {dest}')
                else:
                    self.log.warning(f'{resp.url} status = {resp.status}')
        except Exception as e:
            self.log.warning(f'{url} failed: {e}')
        finally:
            sem.release()

    # async entry point
    async def sched_downloaders(self, num_coros):
        loop = asyncio.get_event_loop()   #prefer get_running_loop in py>=3.7
        sem = asyncio.Semaphore(num_coros)
        async with aiohttp.ClientSession(loop=loop) as session:
            tasks = []
            while True:
                await sem.acquire()
                
                url, dest = self.q.get(True)   #block
                if url is None:
                    self.add_endsignal()    #notify peer threads
                    break
                else:
                    tasks.append(loop.create_task(self.downloader(session, url, dest, sem)))
            # waiting for downloader tasks to finish
            await asyncio.gather(*[t for t in tasks if not t.done()])
            self.log.info('Queue Finished')

if "__main__" == __name__:
    import time, sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(threadName)10s %(name)12s: %(message)s',
        stream=sys.stderr,
    )

    dld = AioDownloader()
    for i in range(30):
        dld.add_url(f"http://httpbin.org/delay/1?a={i}", '/dev/null')
    dld.add_endsignal()

    t0 = time.time()
    log = logging.getLogger('main')    
    log.info('start worker threads')

    dld.start(2, 5)
    dld.join()

    log.info('all workers exit')

    print(f'{time.time()-t0} seconds')
