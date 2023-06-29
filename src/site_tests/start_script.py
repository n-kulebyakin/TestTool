#!/usr/bin/env python
from FTFLibrary import *
# ===================================================
# FTF CUSTOM SCRIPT FOR NORMALIZATION
# Version: '1.0'
# Document_status: 'Status: RELEASED'
# Prepared_by: 'RUSNKUL'
# Date: '2019-10-29'
# ===================================================
# -------------------------------------------------
TCHAPT_NO = '1'
TS_NO = '1'
TC_NO = '1'
t_no = 1
pmm = []
pmp = []


def normalise_superviser(superviser, func=ftf.add_event):
    func('illSetIbit 1 ' + superviser + ' I_T 1')


def normalise_feed(feed, func=ftf.add_event):
    if ftf.getLogicalStatus2IPU(feed, 'C_AVP'):
        avp = ftf.getLogicalStatus2IPU(feed, 'C_AVP')
        func('yardSetStatusTryCycles 1 1 ' + avp + ' Occ')
        func('execGoSeconds 1 15')


def signal_normalise(signal, func=ftf.add_event):
    for check in ('C_BS', 'C_JZ', 'C_JSO', 'C_ZS', 'C_ZSO', 'C_2JS'):
        ipu = ftf.getLogicalStatus2IPU(signal, check)
        if ipu:
            func('yardSetStatusTrySeconds 1 2 ' + ipu + ' Occ')


def normailse_uzs(uzs, func=ftf.add_event):
    c_up = ftf.getLogicalStatus2IPU(uzs, 'C_UP')
    c_pos = ftf.getLogicalStatus2IPU(uzs, 'C_POS')
    if c_up:
        func('yardSetStatusTryCycles 1 1 ' + c_up + ' Occ')
    if c_pos:
        func('yardSetStatusTryCycles 1 1 ' + c_pos + ' LEFT')


def normalise_lineblock(lineblock, func=ftf.add_event):
    if ftf.getLogicalIbitValue(lineblock, 'I_LB') == '2':
        for check in ('C_R_S', 'C_R_GM', 'C_R_KS',
                      'C_R_OV', 'C_R_PV', 'C_R_SN', 'C_R_DSO'):
            ipu = ftf.getLogicalStatus2IPU(lineblock, check)
            if ipu:
                func('yardSetStatusTry 1 ' + ipu + ' Occ')
        func('execGoSeconds 1 15')

    if ftf.checkComponentForLO(lineblock, 'IFP'):
        func('cosCmdSeconds 1 2 IFP ' + lineblock)
        func('cosCmdSeconds 1 20 POK ' + lineblock)


def normalise_uksps(uksps, func=ftf.add_event):
    if ftf.getLogicalIbitValue(uksps, 'I_KG') != '0':
        if ftf.checkComponentForLO(uksps, 'VKS'):
            func('cosCmdSeconds 1 2 VKS ' + uksps)
        elif ftf.checkComponentForLO(uksps, 'COM1'):
            func('cosCmdSeconds 1 2 COM1 ' + uksps)
        if ftf.checkComponentForLO(uksps, 'VKS2'):
            func('cosCmdSeconds 1 2 VKS2 ' + uksps)
        c_kd = ftf.getLogicalStatus2IPU(uksps, 'C_KD')
        if c_kd:
            func('yardSetStatusTrySeconds 1 5 ' + c_kd + ' Occ')
            func('yardSetStatusTrySeconds 1 5 ' + c_kd + ' Free')

def normalise_ways(section, func=ftf.add_event):
    if ftf.getLogicalIbitValue(section, 'I_KM') == '2':
        if ftf.checkComponentForLO(section, 'SEOG'):
            func('cosCmdSeconds 1 2 SEOG ' + section)
            func('cosCmdSeconds 1 10 POK ' + section)

def normalise_ktsm(ktsm, func=ftf.add_event):
    if ftf.checkComponentForLO(ktsm, 'VKTSM'):
        func('cosCmdSeconds 1 2 VKTSM ' + ktsm)
        func('cosCmdSeconds 1 20 POK ' + ktsm)


def normalise_helpblock(helpblock, func=ftf.add_event):
    lineblock = get_hb_lineblock(helpblock)
    if lineblock:
        for check in ('C_EE_UP1', 'C_EE_K1', 'C_EE_K2',
                      'C_EE_K3', 'C_EE_K4', 'C_EE_1IPU',
                      'C_EE_2IPU', 'C_EE_MTTC',):
            func('illSetChcSeconds 1 3 {} {} 2'.format(helpblock, check))
        func('illSetChcSeconds 1 3 {} {} 2'.format(helpblock, 'C_EE_MS'))
        func('illSetChcSeconds 1 3 {} {} 1'.format(helpblock, 'C_EE_AP'))
        setCommandABO(lineblock, func=ftf.add_event)
        for check in ('C_EE_RES', 'C_EE_KS', 'C_EE_UU1', 'C_EE_UU1S',
                      'C_EE_UU1X', 'C_EE_UU1XM', 'C_EE_UU1XS', 'C_EE_UU2',
                      'C_EE_UU2S', 'C_EE_UU2X', 'C_EE_UU2XM', 'C_EE_UU2XMS',
                      'C_EE_UU2XS'):
            func('illSetChcSeconds 1 3 {} {} 2'.format(helpblock, check))
        func('illSetChcSeconds 1 3 {} {} 0'.format(helpblock, 'C_EE_RES'))
        func('illSetChcSeconds 1 3 {} {} 3'.format(helpblock, 'C_EE_MS'))
        func('illSetChcSeconds 1 3 {} {} 0'.format(helpblock, 'C_EE_AP'))
        func('illSetChcSeconds 1 3 {} {} 1'.format(helpblock, 'C_EE_LEX'))
        ftf.add_result(lineblock + ': OUT')


def normailse_cisop(func=ftf.add_event):
    for component in (ftf.getAllComponents('VKNM') +
                      ftf.getAllComponents('OKNM')):
        func('cosCmdSeconds 1 2 ' + ' '.join(component))


def normalise_section(section, func=ftf.add_event):
    if not checkForFictiveSection(section):      
        return
    c_io = ftf.getLogicalStatus2IPU(section, 'C_IO')
    if c_io:
        func('yardSetStatusTry 1 ' + c_io + ' Occ')
    if ftf.getLogicalIbitValue(section, 'I_Z') == '0':
        func('cosCmdSeconds 1 2 SEIR ' + section)
        func('cosCmdSeconds 1 2 POK ' + section)
    if ftf.checkComponentForLO(section, 'VKP'):
        func('cosCmdSeconds 1 2 VKP ' + section)
        func('cosCmdSeconds 1 2 POK ' + section)


def get_check_point_model(point, pmp_pmm=[]):
    out_data = []
    if ftf.getLogicalIbitValue(point, 'I_MAK') != '0':
        pmm_ipu = ftf.getLogicalStatus2IPU(point, 'C_PMM')
        pmp_ipu = ftf.getLogicalStatus2IPU(point, 'C_PMP')
        if pmm_ipu not in pmp_pmm:
            out_data.append(pmm_ipu)
        if pmp_ipu not in pmp_pmm:
            out_data.append(pmp_ipu)
    return out_data


def get_hb_lineblock(helpblock):
    arrayOfBackObjects = traceTo(helpblock, '0',
                                 STOP_TRACE_TYPES + ('POINT', 'SECTION'))
    arrayOfBackObjects = [x for x in arrayOfBackObjects if len(x) > 2]

    lineblock = [x for x in arrayOfBackObjects
                 if ftf.getLogicalType(x) in
                 STOP_TRACE_TYPES + ('POINT', 'SECTION')][0]
    if ftf.getLogicalType(lineblock) == 'LINEBLOCK':
        return lineblock


def create_start_cp(t_no=1):
    pmp_pmm = []
    tc_id = '%s.%s.%s.%d' % (TCHAPT_NO, TS_NO, TC_NO, t_no)
    ftf.write_testcase_header(tc_id, '')
    ftf.set_id(tc_id)
    ftf.set_comment('Start interlocking')
    if t_no == 1:
        ftf.add_init('ilsInitCurrent 1')
        ftf.add_init('ilsLoadCurrent 1')
        ftf.add_init('execGoSeconds 1 10')
    ftf.add_init('calcTraceOn 1')
    for superviser in ftf.getLogicalNamesofType('SUPERVISER'):
        normalise_superviser(superviser)
    for feed in ftf.getLogicalNamesofType('FEED'):
        normalise_feed(feed)
    for section in ftf.getLogicalNamesofType('SECTION'):
        normalise_section(section)
        normalise_ways(section)
    for signal in ftf.getLogicalNamesofType('SIGNAL'):
        signal_normalise(signal)
    for point in ftf.getLogicalNamesofType('POINT'):
        pmp_pmm += get_check_point_model(point, pmp_pmm)
    for pmp_pmm_ipu in pmp_pmm:
        ftf.add_event('yardSetStatusTry 1 ' + pmp_pmm_ipu + ' Occ')
    for point in ftf.getLogicalNamesofType('POINT'):
        switch_point_to_pos(point, 'M_SW=2')
    for uzs in (ftf.getLogicalNamesofType('BUFFER') +
                ftf.getLogicalNamesofType('UZS')):
        normailse_uzs(uzs)
    for lineblock in ftf.getLogicalNamesofType('LINEBLOCK'):
        normalise_lineblock(lineblock)
    for uksps in ftf.getLogicalNamesofType('INTERFACE'):
        normalise_uksps(uksps)
        normalise_ktsm(uksps)
    for helpblock in ftf.getLogicalNamesofType('HELPBLOCK_R4'):
        normalise_helpblock(helpblock)
    for helpblock in ftf.getLogicalNamesofType('HELPBLOCK'):
        normalise_helpblock(helpblock)
    normailse_cisop()
    ftf.add_event('execGoSeconds 1 185')
    ftf.add_event('ilsCheckpointSave 1 StartCP')
    for point in ftf.getLogicalNamesofType('POINT'):
        switch_point_to_pos(point, 'M_SW=1')
        if is_relay_point(point):
            ftf.add_result(point + ': PK_IND')
        else:
            ftf.add_result(point + ': PLUS_IND')
    ftf.add_event('execGoSeconds 1 185')
    ftf.add_event('ilsCheckpointSave 1 StartCP_PLUS')
    ftf.write_subtest_obj()
    ftf.write_testcase_footer()
    t_no += 1

    return t_no


if __name__ == "__main__":
    ftf.create_xml_file(ftf.OutputDataPath + 'create_cp.xml')
    ftf.write_file_header()
    ftf.write_function_header('START SCRIPT')
    ftf.write_testsuite_header('START SCRIPT')
    create_start_cp()
    ftf.write_testsuite_footer()
    ftf.write_function_footer()
    ftf.write_file_footer()
    ftf.close_xml_file()
