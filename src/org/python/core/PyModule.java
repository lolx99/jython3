// Copyright (c) Corporation for National Research Initiatives
package org.python.core;

import org.python.expose.ExposedDelete;
import org.python.expose.ExposedGet;
import org.python.expose.ExposedMethod;
import org.python.expose.ExposedNew;
import org.python.expose.ExposedSet;
import org.python.expose.ExposedType;

/**
 * The Python Module object.
 *
 */
@ExposedType(name = "module")
public class PyModule extends PyObject implements Traverseproc {
    public static final PyType TYPE = PyType.fromClass(PyModule.class);

    private final PyObject moduleDoc = new PyString(
        "module(name[, doc])\n" +
        "\n" +
        "Create a module object.\n" +
        "The name must be a string; the optional doc argument can have any type.");

    /** The module's mutable dictionary */
    @ExposedGet
    public PyObject __dict__;

    public PyModule() {
        super();
    }

    public PyModule(PyType subType) {
        super(subType);
    }

    public PyModule(PyType subType, String name) {
        super(subType);
        module___init__(new PyString(name), Py.None);
    }

    public PyModule(String name) {
        this(name, null);
    }

    public PyModule(String name, PyObject dict) {
        super(TYPE);
        __dict__ = dict;
        module___init__(new PyUnicode(name), Py.None);
    }

    @ExposedNew
    @ExposedMethod
    final void module___init__(PyObject[] args, String[] keywords) {
        ArgParser ap = new ArgParser("__init__", args, keywords, new String[] {"name", "doc"});
        PyObject name = ap.getPyObject(0);
        PyObject docs = ap.getPyObject(1, Py.None);
        module___init__(name, docs);
    }

    private void module___init__(PyObject name, PyObject doc) {
        ensureDict();
        __dict__.__setitem__("__name__", name);
        __dict__.__setitem__("__doc__", doc);
        if (name.equals(new PyUnicode("__main__"))) {
            __dict__.__setitem__("__builtins__", Py.getSystemState().modules.__finditem__("__builtin__"));
            __dict__.__setitem__("__package__", Py.None);
        }
    }

    public PyObject fastGetDict() {
        return __dict__;
    }

    public PyObject getDict() {
        return __dict__;
    }

    @ExposedSet(name = "__dict__")
    public void setDict(PyObject newDict) {
        throw Py.TypeError("readonly attribute");
    }

    @ExposedDelete(name = "__dict__")
    public void delDict() {
        throw Py.TypeError("readonly attribute");
    }

    protected PyObject impAttr(String name) {
        if (__dict__ == null) {
            return null;
        }
        PyObject path = __dict__.__finditem__("__path__");
        if (path == null) {
            path = new PyList();
        }
        PyObject pyName = __dict__.__finditem__("__name__");
        if (pyName == null) {
            return null;
        }
        PyObject attr = null;
        String fullName = (pyName.__str__().toString() + '.' + name).intern();
        if (path == Py.None) {
            // XXX: disabled
            //attr = imp.loadFromClassLoader(fullName,
            //                               Py.getSystemState().getClassLoader());
        } else if (path instanceof PyList) {
            attr = imp.find_module(name, fullName, (PyList)path);
        } else {
            throw Py.TypeError("__path__ must be list or None");
        }

        if (attr == null) {
            attr = PySystemState.packageManager.lookupName(fullName);
        }

        if (attr != null) {
            // Allow a package component to change its own meaning
            PyObject found = Py.getSystemState().modules.__finditem__(fullName);
            if (found != null) {
                attr = found;
            }
            __dict__.__setitem__(name, attr);
            return attr;
        }

        return null;
    }

    public void __setattr__(String name, PyObject value) {
        module___setattr__(name, value);
    }

    @ExposedMethod
    final void module___setattr__(String name, PyObject value) {
        if (name != "__dict__") {
            ensureDict();
        }
        super.__setattr__(name, value);
    }

    public void __delattr__(String name) {
        module___delattr__(name);
    }

    @ExposedMethod
    final void module___delattr__(String name) {
        super.__delattr__(name);
    }

    public String toString()  {
        return module_toString();
    }

    @ExposedMethod(names = {"__repr__"})
    final String module_toString()  {
        PyObject name = null;
        PyObject filename = null;

        if (__dict__ != null) {
            name = __dict__.__finditem__("__name__");
            filename = __dict__.__finditem__("__file__");
        }
        if (name == null) {
            name = new PyString("?");
        }
        if (filename == null) {
            return String.format("<module '%s' (built-in)>", name);
        }
        return String.format("<module '%s' from '%s'>", name, filename);
    }

    public PyObject __dir__() {
        // Some special casing to ensure that classes deriving from PyModule
        // can use their own __dict__. Although it would be nice to do this in
        // PyModuleDerived, current templating in gderived.py does not support
        // including from object, then overriding a specific method.
        PyObject d;
        if (this instanceof PyModuleDerived) {
            d = __findattr_ex__("__dict__");
        } else {
            d = __dict__;
        }
        if (d == null ||
                !(d instanceof PyDictionary ||
                  d instanceof PyStringMap ||
                  d instanceof PyDictProxy)) {
            throw Py.TypeError(String.format("%.200s.__dict__ is not a dictionary",
                    getType().fastGetName().toLowerCase()));
        }
        return d.invoke("keys");
    }

    private void ensureDict() {
        if (__dict__ == null) {
            __dict__ = new PyStringMap();
        }
    }


    /* Traverseproc implementation */
    @Override
    public int traverse(Visitproc visit, Object arg) {
        return __dict__ == null ? 0 : visit.visit(__dict__, arg);
    }

    @Override
    public boolean refersDirectlyTo(PyObject ob) {
        return ob != null && ob == __dict__;
    }
}
