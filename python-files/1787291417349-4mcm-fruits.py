def fruits(tuple_of_fruits):
    good_fruits = {}
    
    for fruit in tuple_of_fruits:
        name = fruit['name']
        shape = fruit['shape']
        mass = fruit['mass']
        volume = fruit['volume']
        
        is_good = (shape == 'sphere' and 
                   300 <= mass <= 600 and 
                   100 <= volume <= 500)
        
        if is_good:
            if name in good_fruits:
                good_fruits[name] += 1
            else:
                good_fruits[name] = 1
    
    return good_fruits

print(fruits((
    {'name':'apple', 'shape': 'sphere', 'mass': 350, 'volume': 120},
    {'name':'mango', 'shape': 'square', 'mass': 150, 'volume': 120}, 
    {'name':'lemon', 'shape': 'sphere', 'mass': 300, 'volume': 100},
    {'name':'apple', 'shape': 'sphere', 'mass': 500, 'volume': 250})))
