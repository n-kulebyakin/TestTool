
# ----------------------------------------------------
test_file_name = ''
test_init_array = []
test_event_array = []
test_result_array = []

out_array = []
# ----------------------------------------------------

def create_xml_file(fileName='ALL_TI.xml'):
    global FileName
    FileName = fileName

def write_file_header(out_array):
    out_array.append('<?xml version=\'1.0\' encoding=\'UTF-8\'?>')
    out_array.append('<Functions>')


def write_function_header(name=''):
    out_array.append('   <Function name=\'' + name + '\'>')


def write_testsuite_header(name=''):
    out_array.append('      <TestSuite name=\'' + name + '\'>')


def write_testcase_header(test_id='1.1.1.1', test_case_name=''):
    out_array.append('         <TestCase id=\'' + test_id + '\' ' + 'name=\'' + test_case_name + '\'>')
    test_init_array.clear()
    test_event_array.clear()
    test_result_array.clear()


def set_id(test_id='1.1.1.1'):
    out_array.append('            <Test id=\'' + test_id + '\'>')


def set_comment(test_comment=''):
    out_array.append('               <Comment>' + test_comment + '</Comment>')


def add_init(event):
    test_init_array.append(18 * ' ' + '<Event>' + event + '</Event>')


def add_event(event):
    test_event_array.append(18 * ' ' + '<Event>' + event + '</Event>')


def add_result(result):
    test_result_array.append(18 * ' ' + '<Result>' + result + '</Result>')


def write_subtest_obj():
    out_array.append('               <InitEvents>')
    for event in test_init_array:
        out_array.append(event)
    out_array.append('               </InitEvents>')
    out_array.append('               <TestEvents>')
    for event in test_event_array:
        out_array.append(event)
    out_array.append('               </TestEvents>')
    out_array.append('               <ExpectedResults>')
    for Results in test_result_array:
        out_array.append(Results)
    out_array.append('               </ExpectedResults>')


def write_testcase_footer():
    out_array.append('            </Test>')
    out_array.append('         </TestCase>')


def write_testsuite_footer():
    out_array.append('      </TestSuite>')


def write_function_footer():
    out_array.append('   </Function>')


def write_file_footer():
    out_array.append('</Functions>')


def close_xml_file(file_name):
    outFile = open(file_name, 'w')
    outFile.write('\n'.join(out_array))
    outFile.close()
    out_array.clear()
