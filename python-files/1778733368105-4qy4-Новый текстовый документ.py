>>> def calculate():
...     print "--- Калькулятор для Python 2.6.6 ---"
...
...     try:
...         # Используем raw_input, так как в 2.6 input() небезопасен
...         num1 = float(raw_input("Введите первое число: "))
...         operation = raw_input("Выберите операцию (+, -, *, /): ")
...         num2 = float(raw_input("Введите второе число: "))
...
  File "<stdin>", line 9

    ^
IndentationError: unexpected unindent
>>>         if operation == '+':
  File "<stdin>", line 1
    if operation == '+':
    ^
IndentationError: unexpected indent
>>>             result = num1 + num2
  File "<stdin>", line 1
    result = num1 + num2
    ^
IndentationError: unexpected indent
>>>         elif operation == '-':
  File "<stdin>", line 1
    elif operation == '-':
    ^
IndentationError: unexpected indent
>>>             result = num1 - num2
  File "<stdin>", line 1
    result = num1 - num2
    ^
IndentationError: unexpected indent
>>>         elif operation == '*':
  File "<stdin>", line 1
    elif operation == '*':
    ^
IndentationError: unexpected indent
>>>             result = num1 * num2
  File "<stdin>", line 1
    result = num1 * num2
    ^
IndentationError: unexpected indent
>>>         elif operation == '/':
  File "<stdin>", line 1
    elif operation == '/':
    ^
IndentationError: unexpected indent
>>>             if num2 == 0:
  File "<stdin>", line 1
    if num2 == 0:
    ^
IndentationError: unexpected indent
>>>                 print "Ошибка: Деление на ноль!"
  File "<stdin>", line 1
    print "Ошибка: Деление на ноль!"
    ^
IndentationError: unexpected indent
>>>                 return
  File "<stdin>", line 1
    return
    ^
IndentationError: unexpected indent
>>>             result = num1 / num2
  File "<stdin>", line 1
    result = num1 / num2
    ^
IndentationError: unexpected indent
>>>         else:
  File "<stdin>", line 1
    else:
    ^
IndentationError: unexpected indent
>>>             print "Ошибка: Неверная операция!"
  File "<stdin>", line 1
    print "Ошибка: Неверная операция!"
    ^
IndentationError: unexpected indent
>>>             return
  File "<stdin>", line 1
    return
    ^
IndentationError: unexpected indent
>>>
>>>         # В Python 2.6 print - это оператор, а не функция
...         print "Результат: ", result
  File "<stdin>", line 2
    print "Результат: ", result
    ^
IndentationError: unexpected indent
>>>
>>>     except ValueError:
  File "<stdin>", line 1
    except ValueError:
    ^
IndentationError: unexpected indent
>>>         print "Ошибка: Нужно вводить только числа!"
  File "<stdin>", line 1
    print "Ошибка: Нужно вводить только числа!"
    ^
IndentationError: unexpected indent
>>>     except Exception as e:
  File "<stdin>", line 1
    except Exception as e:
    ^
IndentationError: unexpected indent
>>>         print "Произошла ошибка:", e
  File "<stdin>", line 1
    print "Произошла ошибка:", e
    ^
IndentationError: unexpected indent
>>>
>>> if __name__ == "__main__":
...     calculate()