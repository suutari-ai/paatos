

import contextlib
import tempfile
import requests


class SimpleDocumentInfo(DocumentInfo):
    def __init__(self, url):
        self.url = url

    @contextlib.contextmanager
    def _open_remote_xml_file2(self):
        max_size = (16 * 1024 * 1024)  # 16 MiB
        with tempfile.SpooledTemporaryFile(max_size=max_size) as tmp:
            tmp.write(requests.get(self.url).content)
            tmp.flush()
            tmp.seek(0)
            zipf = zipfile.ZipFile(tmp)
            name_list = zipf.namelist()
            xml_names = [x for x in name_list if x.endswith('.xml')]
            if len(xml_names) == 0:
                # FIXME: Workaround for a silly bug
                xml_names = [x for x in name_list if re.match(r'\w+\d+xml_', x)]
                if len(xml_names) != 1:
                    raise IOError("No XML file in ZIP: {}".format(self.url))
            if len(xml_names) > 1:
                raise IOError("Too many XML files in ZIP: {}".format(self.url))
            yield zipf.open(xml_names[0])


URLS = """
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202012-03-15%20Aslk%204%20Pk%20Su.zip
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202012-09-27%20Aslk%2010%20Pk%20Su.zip
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202012-02-02%20Aslk%201%20Pk%20Su.zip
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202012-04-26%20Aslk%206%20Pk%20Su.zip
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202012-02-16%20Aslk%202%20Pk%20Su.zip
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202013-08-29%20Aslk%208%20El%20Su.zip
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202013-08-29%20Aslk%208%20Pk%20Su.zip
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202014-06-17%20Aslk%205%20El%20Su.zip
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202016-03-31%20Aslk%203%20El%20Su.zip
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202016-03-31%20Aslk%203%20Pk%20Su.zip
http://openhelsinki.hel.fi/files/Asuntolautakunta_60014/Kv%202012-04-12%20Aslk%205%20Pk%20Su.zip
http://openhelsinki.hel.fi/files/Ymparistolautakunta_12800/Ymk%202016-03-15%20Ylk%205%20El%20Su.zip
""".strip().split()


def compare(urls=URLS):
    import time

    len1 = 0
    len2 = 0

    times1 = {}
    times2 = {}

    for url in urls:
        doc_info = SimpleDocumentInfo(url)

        print('Doing 1 for {}'.format(url))
        t1 = time.time()
        with doc_info._open_remote_xml_file() as fp:
            len1 += len(fp.read())
        t2 = time.time()
        times1[url] = t2 - t1

        print('Doing 2 for {}'.format(url))
        t1 = time.time()
        with doc_info._open_remote_xml_file2() as fp:
            len2 += len(fp.read())
        t2 = time.time()
        times2[url] = t2 - t1

    print('Total lengths:', len1, len2)

    print('Total time 1:', sum(times1.values()))
    print('Total time 2:', sum(times2.values()))

    return {'times1': times1, 'times2': times2}
