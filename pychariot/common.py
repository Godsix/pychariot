# -*- coding: utf-8 -*-
"""
Created on Fri Sep 16 16:15:49 2022

@author: 皓
"""
import os.path as osp
import logging
import locale
from functools import wraps
import operator
from ctypes import (CDLL, POINTER, create_string_buffer, create_unicode_buffer,
                    byref, c_int,  c_ulong, c_char_p, c_char, c_wchar,
                    c_wchar_p, cast)

try:
    ENCODING = locale.getencoding()
except AttributeError:
    # 3.11 deprecated,3.15 remove.Use getencoding() instead.
    ENCODING = locale.getdefaultlocale()[1]  # pylint: disable=deprecated-method


class UnSupportError(Exception):
    pass


class BaseParam:
    def __init__(self, datatype):
        self.datatype = self._check_datatype(datatype)

    @classmethod
    def _check_datatype(cls, datatype):
        assert isinstance(datatype, type), datatype
        if hasattr(datatype, 'from_param'):
            return datatype
        if issubclass(datatype, (str, bytes)):
            return datatype
        name = datatype.__name__
        raise TypeError(f'Datatype must be a ctypes or str, bytes, but {name}')

    @classmethod
    def encode(cls, data):
        if isinstance(data, str):
            return data.encode(ENCODING)
        return data

    @classmethod
    def decode(cls, data):
        if isinstance(data, bytes):
            return data.decode(ENCODING)
        return data


class BaseIn(BaseParam):
    pass


class ParamIn(BaseIn):
    def __init__(self, datatype, cast_type=None):
        super().__init__(datatype)
        assert cast_type is None or hasattr(cast_type, 'from_param'), cast_type
        self.cast_type = cast_type

    def get_ctypes(self):
        if hasattr(self.datatype, 'from_param'):
            return tuple([self.datatype])
        if issubclass(self.datatype, bytes):
            ctype = c_char
        if issubclass(self.datatype, str):
            ctype = c_wchar
        dtype = self.cast_type if self.cast_type else POINTER(ctype)
        return dtype, c_ulong

    def __call__(self, value):
        if hasattr(self.datatype, 'from_param'):
            return tuple([self.datatype(value)])
        if issubclass(self.datatype, str):
            format_value = self.decode(value)
        if issubclass(self.datatype, bytes):
            format_value = self.encode(value)
        length = len(format_value)
        if self.cast_type:
            format_value = cast(format_value, self.cast_type)
        return format_value, length


class BaseOut(BaseParam):

    def __init__(self, datatype, maxlength=None, cast_type=None):
        super().__init__(datatype)
        self.maxlength = maxlength
        self.cast_type = cast_type
        self.data = None
        self.length = 0

    def get_ctypes(self):  # pylint: disable=inconsistent-return-statements
        if hasattr(self.datatype, 'from_param'):
            return tuple([POINTER(self.datatype)])
        if issubclass(self.datatype, bytes):
            dtype = self.cast_type if self.cast_type else POINTER(c_char)
            return dtype, c_ulong, POINTER(c_ulong)
        if issubclass(self.datatype, str):
            dtype = self.cast_type if self.cast_type else POINTER(c_wchar)
            return dtype, c_ulong, POINTER(c_ulong)

    def get_result(self):  # pylint: disable=inconsistent-return-statements
        if issubclass(self.datatype, bytes):
            return self.decode(self.data.value)
        if issubclass(self.datatype, str):
            return self.data.value
        if hasattr(self.data, 'value'):
            return self.data.value


class ParamOut(BaseOut):

    def __call__(self):
        if hasattr(self.datatype, 'from_param'):
            self.data = self.datatype()
            return tuple([byref(self.data)])
        if issubclass(self.datatype, bytes):
            self.data = create_string_buffer(b"\0", self.maxlength)
        if issubclass(self.datatype, str):
            self.data = create_unicode_buffer("\0", self.maxlength)
        self.length = c_ulong()
        return self.data, c_ulong(self.maxlength), byref(self.length)


class ParamInOut(BaseOut, BaseIn):

    def __call__(self, value):
        if hasattr(self.datatype, 'from_param'):
            self.data = self.datatype(value)
            return tuple([byref(self.data)])
        if issubclass(self.datatype, bytes):
            self.data = create_string_buffer(self.encode(value),
                                             self.maxlength)
        if issubclass(self.datatype, str):
            self.data = create_unicode_buffer(self.decode(value),
                                              self.maxlength)
        self.length = c_ulong()
        return self.data, c_ulong(self.maxlength), byref(self.length)


class CFuncDecorator:
    def __init__(self):
        self.logger = logging.getLogger()
        self.params = {}

    def set_params(self, func_name, restype, *argtypes):
        self.params[func_name] = restype, *argtypes

    @classmethod
    def get_ctypes(cls, obj):
        if hasattr(obj, 'from_param'):
            return obj
        if isinstance(obj, BaseParam):
            return obj.get_ctypes()
        if issubclass(obj, str):
            return c_wchar_p
        if issubclass(obj, bytes):
            return c_char_p

        raise TypeError(f'Unsupport type:{type(obj).__name__}')

    def get_param_ctypes(self, func_name):
        if func_name not in self.params:
            return None
        args = self.params[func_name]
        cargs = []
        for arg in args:
            ret = self.get_ctypes(arg)
            if isinstance(ret, (tuple, list)):
                cargs.extend(ret)
            else:
                cargs.append(ret)
        return tuple(cargs)

    def init_cdll(self, cdll_object):
        assert isinstance(cdll_object, CDLL)
        dll_name = osp.basename(cdll_object._name)  # pylint: disable=protected-access
        for name in self.params:
            if hasattr(cdll_object, name):
                func = getattr(cdll_object, name)
                restype, *argtypes = self.get_param_ctypes(name)
                func.restype = restype
                func.argtypes = argtypes
            else:
                self.logger.error("%s have no function: %s", dll_name, name)


class CHRDecorator(CFuncDecorator):
    def __init__(self):
        super().__init__()
        self.vcontrol = {}
        self.version = None

    def check_version(self, name):
        if self.version is None:
            return True
        if name not in self.vcontrol:
            return True
        _text, op, ver = self.vcontrol[name]
        if op(self.version, ver):
            return True
        return False

    def raise_version(self, name):
        if self.check_version(name) is False:
            text, _op, ver = self.vcontrol[name]
            raise UnSupportError(
                f'{name} is valid {text} {ver}, current is {self.version}')

    def init_cdll(self, cdll_object):
        assert isinstance(cdll_object, CDLL)
        dll_name = osp.basename(cdll_object._name)  # pylint: disable=protected-access
        for name in self.params:
            if hasattr(cdll_object, name):
                func = getattr(cdll_object, name)
                restype, *argtypes = self.get_param_ctypes(name)
                func.restype = restype
                func.argtypes = argtypes
            else:
                if self.check_version(name) is not False:
                    self.logger.error("%s have no function: %s",
                                      dll_name,
                                      name)

    def __call__(self, *param_args):
        def decorator(func):
            func_name = func.__name__
            self.set_params(func_name, c_int, *param_args)

            @wraps(func)
            def wrapper(*args, **kwargs):
                self, *param = args
                dll = getattr(self, 'dll')
                dll_func = getattr(dll, func_name)
                format_args = []
                out_params = []
                param_iter = iter(param)
                for item in param_args:
                    if isinstance(item, BaseParam):
                        if isinstance(item, BaseOut):
                            out_params.append(item)
                        if isinstance(item, BaseIn):
                            format_args.extend(item(next(param_iter)))
                        else:
                            format_args.extend(item())
                    else:
                        if issubclass(item, bytes):
                            f_value = BaseParam.encode(next(param_iter))
                        elif issubclass(item, str):
                            f_value = BaseParam.decode(next(param_iter))
                        else:
                            f_value = item(next(param_iter))
                        format_args.append(f_value)
                ret = dll_func(*format_args, **kwargs)
                if out_params:
                    out_values = [x.get_result() for x in out_params]
                    return ret, *out_values
                return ret
            return wrapper
        return decorator

    def param(self, *argtypes):
        def decorator(func):
            func_name = func.__name__
            self.set_params(func_name, c_int, *argtypes)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def since(self, version):
        def decorator(func):
            func_name = func.__name__
            self.vcontrol[func_name] = ('since', operator.ge, version)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

    def until(self, version):
        def decorator(func):
            func_name = func.__name__
            self.vcontrol[func_name] = ('until', operator.le, version)

            @wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator


def singleton(cls):
    instances = {}

    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return get_instance
