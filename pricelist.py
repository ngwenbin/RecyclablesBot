# ## Price list for papers, clothes
# # price per kg
# paper_price = 0.04
# clothes_price = 0.8

# def price_point(item, low, high):
#     if item == "papers":
#         price = paper_price
#     elif item == "clothes":
#         price = clothes_price
#     price_text =''
#     for x in range(low, high):
#         price_text += ("{0}KG to {1}KG: ${2:.2f} to ${3:.2f}\n".format((x)*10,
#                                                                         (x+1)*10,
#                                                                         (x)*10*price,
#                                                                         (x+1)*10*price))
#     return price_text