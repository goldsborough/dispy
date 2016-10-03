# dispy

[![GitHub license](https://img.shields.io/github/license/mashape/apistatus.svg?style=flat-square)](http://goldsborough.mit-license.org)

A tiny Python bytecode disassembler.

`dispy` emulates the behavior of `dis.dis` in that it will take a function, method, code object or code string and print a pretty representation of the corresponding bytecode. See [here]() for a blog post on `dis.dis` and bytecode in general.

## Usage

To use `dispy`, simply import the package and call the `dispy.dis()` method with any of the aforementioned argument types. For example:

```python
def foo():
    a = 1
    b = 2
    return math.tanh(a * b)

dispy.dis(foo)
```

will print:

```
0       0 LOAD_CONST        1 (1)
        3 STORE_FAST        0 (a)

1       6 LOAD_CONST        2 (2)
        9 STORE_FAST        1 (b)

2       12 LOAD_GLOBAL      0 (math)
        15 LOAD_ATTR        1 (tanh)
        18 LOAD_FAST        0 (a)
        21 LOAD_FAST        1 (b)
        24 BINARY_MULTIPLY
        25 CALL_FUNCTION
        26 POP_TOP
        27 STOP_CODE
        28 RETURN_VALUE
```

## Hackability

The source is very small (~300 LOC), so feel free to reuse, fork and modify.

## License

This project is released under the [MIT License](http://goldsborough.mit-license.org). For more information, see the LICENSE file.

## Authors

[Peter Goldsborough](http://goldsborough.me) + [cat](https://goo.gl/IpUmJn) :heart:

<a href="https://gratipay.com/~goldsborough/"><img src="http://img.shields.io/gratipay/goldsborough.png?style=flat-square"></a>
