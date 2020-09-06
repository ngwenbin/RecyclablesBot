paperprice = 0.06
clothesprice = 0.20

def price_point(item, low, high):
    if item == "papers":
        price = paperprice
    else:
        price = clothesprice
    price_text =''
    for x in range(low, high):
        price_text += ("{0}KG to {1}KG: ${2:.2f} to ${3:.2f}\n".format((x)*10,
                                                                        (x+1)*10,
                                                                        (x)*10*price,
                                                                        (x+1)*10*price))
    return price_text