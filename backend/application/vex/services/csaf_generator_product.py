from typing import Optional

from application.core.models import Branch, Product
from application.vex.services.csaf_generator_helpers import get_product_id
from application.vex.types import (
    CSAF_Branch_Category,
    CSAFFullProductName,
    CSAFProductBranch,
    CSAFProductIdentificationHelper,
    CSAFProductTree,
)


def append_product_to_product_tree(
    product_tree: CSAFProductTree,
    product: Product,
    branch: Optional[Branch],
) -> None:

    found = False
    for product_family_branch in product_tree.branches:
        if product_family_branch.name == product.name:
            found = True
            break
    if not found:
        product_family_branch = CSAFProductBranch(
            name=product.name,
            category=CSAF_Branch_Category.CSAF_BRANCH_CATEGORY_PRODUCT_FAMILY,
            branches=[],
        )
        product_tree.branches.append(product_family_branch)

    product_id = get_product_id(product, branch)

    if not branch:
        if product_family_branch.branches is None:
            raise ValueError("Product family branches should not be None")
        for product_name_branch in product_family_branch.branches:
            if product_name_branch.product and product_name_branch.product.product_id == product_id:
                return

        new_product_full_name = _create_product(product, branch)
        new_product_branch = CSAFProductBranch(
            name=product.name,
            category=CSAF_Branch_Category.CSAF_BRANCH_CATEGORY_PRODUCT_NAME,
            product=new_product_full_name,
        )
        product_family_branch.branches.append(new_product_branch)
    else:
        if product_family_branch.branches is None:
            raise ValueError("Product family branches should not be None")
        for version_branch in product_family_branch.branches:
            if version_branch.product and version_branch.product.product_id == product_id:
                return

        new_product_full_name = _create_product(product, branch)
        new_product_branch = CSAFProductBranch(
            name=f"{product.name}:{branch.name}",
            category=CSAF_Branch_Category.CSAF_BRANCH_CATEGORY_PRODUCT_VERSION,
            product=new_product_full_name,
        )
        product_family_branch.branches.append(new_product_branch)


def _create_product(product: Product, branch: Optional[Branch]) -> CSAFFullProductName:
    product_identification_helper = None
    if branch:
        if branch.purl or branch.cpe23:
            purl = branch.purl if branch.purl else None
            cpe = branch.cpe23 if branch.cpe23 else None
            product_identification_helper = CSAFProductIdentificationHelper(purl=purl, cpe=cpe)
    else:
        if product.purl or product.cpe23:
            purl = product.purl if product.purl else None
            cpe = product.cpe23 if product.cpe23 else None
            product_identification_helper = CSAFProductIdentificationHelper(purl=purl, cpe=cpe)

    product_name = f"{product.name}:{branch.name}" if branch else product.name

    full_product_name = CSAFFullProductName(
        name=product_name,
        product_id=get_product_id(product, branch),
        product_identification_helper=product_identification_helper,
    )

    return full_product_name
