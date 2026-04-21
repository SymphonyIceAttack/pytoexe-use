#!/usr/bin/env python
# coding: utf-8

# In[17]:


list_mult = [3,2,7,6,5,4,3,2]


# In[18]:


nums = input("Cual es tu RUN sin el dígito verificador? \n")


# In[19]:


sum_nums = 0
for num, mult in zip(nums, list_mult):
    multiplication = int(num)*mult
    sum_nums += multiplication

ver_dig = sum_nums%11

print("Tu dígito verificador es: ", ver_dig)

