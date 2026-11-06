def chinese_remainder_theorem(remainders, moduli):
    from functools import reduce
    def extended_gcd(modulo_product_i, modulo_i):
        if modulo_product_i == 0:
            return modulo_i, 0, 1
        greatest_common_divisor, x1, y1 = extended_gcd(modulo_i % modulo_product_i, modulo_product_i)
        x = y1 - (modulo_i // modulo_product_i) * x1
        y = x1
        return greatest_common_divisor, x, y

    def mod_inv(modulo_product_i, modulo_i):
        greatest_common_divisor, x, _ = extended_gcd(modulo_product_i, modulo_i)
        if greatest_common_divisor != 1:
            raise ValueError("Modular inverse does not exist")
        return x % modulo_i

    moduli_product = reduce(lambda x, y: x * y, moduli)
    result = 0
    for remainder_i, modulo_i in zip(remainders, moduli):
        moduli_product_i = moduli_product // modulo_i
        result += remainder_i * moduli_product_i * mod_inv(moduli_product_i, modulo_i)
    return result % moduli_product