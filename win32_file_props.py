import win32api
import typing


def get_file_properties(fname):
    """
    Read all properties of the given file return them as a dictionary.
    """
    propNames = ('Comments', 'InternalName', 'ProductName', 'CompanyName',
                 'LegalCopyright', 'ProductVersion', 'FileDescription',
                 'LegalTrademarks', 'PrivateBuild', 'FileVersion',
                 'OriginalFilename', 'SpecialBuild')

    props = {
        'FixedFileInfo': None,
        'StringFileInfo': None,
        'FileVersion': None
    }

    try:
        # backslash as parm returns dictionary of numeric info corresponding to VS_FIXEDFILEINFO struc
        fixedInfo = win32api.GetFileVersionInfo(fname, '\\')
        props['FixedFileInfo'] = fixedInfo
        props['FileVersion'] = "%d.%d.%d.%d" % (
            fixedInfo['FileVersionMS'] / 65536, fixedInfo['FileVersionMS'] %
            65536, fixedInfo['FileVersionLS'] / 65536,
            fixedInfo['FileVersionLS'] % 65536)

        # \VarFileInfo\Translation returns list of available (language, codepage)
        # pairs that can be used to retreive string info. We are using only the first pair.
        lang, codepage = win32api.GetFileVersionInfo(
            fname, '\\VarFileInfo\\Translation')[0]

        # any other must be of the form \StringfileInfo\%04X%04X\parm_name, middle
        # two are language/codepage pair returned from above

        strInfo = {}
        for propName in propNames:
            strInfoPath = u'\\StringFileInfo\\%04X%04X\\%s' % (lang, codepage,
                                                               propName)
            ## print str_info
            strInfo[propName] = win32api.GetFileVersionInfo(fname, strInfoPath)

        props['StringFileInfo'] = strInfo
    except:
        pass

    return props


def get_file_description(fname) -> typing.Union[str, None]:
    """
    returns file description or None if not possible
    """
    proc_props = get_file_properties(fname)
    try:
        desc = proc_props['StringFileInfo']['FileDescription']
        return desc
    except Exception:
        return None
