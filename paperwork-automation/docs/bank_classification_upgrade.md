# Bank Transaction Classification System Upgrade

## Overview

The bank transaction classification system has been upgraded from simple string mapping to a sophisticated tuple-based system that supports:

- **Amount-based classification**: Different handling for large vs small transactions
- **Regex pattern matching**: Flexible description matching with complex patterns
- **Combined matching**: Match both description AND amount for precise classification
- **Order-based evaluation**: Rules evaluated in list order (first match wins)
- **Enhanced metadata**: Automatic determination of documentation requirements

## Key Files

- **`configs/bank_desc.py`**: Enhanced classification system (main interface)
- **`configs/bank_transaction_rules.py`**: Transaction rule definitions (tuple-based rules)
- **`scripts/process_bank_transactions.py`**: Updated to use enhanced system with amount data

## New System Features

### 1. Amount-Based Classification

The system can now classify transactions differently based on their amounts:

```python
# Large UBER transactions (>$1000) require extra documentation
(TransactionMatchRule(
    description_pattern=re.compile(r'\bUBER\b', re.IGNORECASE),
    amount_pattern=(1000.0, float('inf')),
    priority=10
), {
    "品名": "收入进账",
    "付款详情": "Uber外卖大额进账",
    "单据号": True,  # Large amounts need documentation
    "附件": True,
})

# Regular UBER transactions
(TransactionMatchRule(
    description_pattern=re.compile(r'\bUBER\b', re.IGNORECASE),
    priority=80
), {
    "品名": "收入进账",
    "付款详情": "Uber外卖佣金",
    "单据号": False,  # Regular amounts don't need extra docs
    "附件": False,
})
```

### 2. Regex Pattern Matching

Complex patterns can now be matched using regular expressions:

```python
# BMO internal transfer pattern
(TransactionMatchRule(
    description_pattern=re.compile(r'0782-1931-\d{3}\s+\d{4}', re.IGNORECASE),
    priority=1
), {
    "品名": "内部转款",
    "付款详情": "BMO内部转款",
})

# Payroll patterns with various spellings
(TransactionMatchRule(
    description_pattern=re.compile(r'PAYROLL|PAY\s*ROLL|BUSINESS\s+PAD', re.IGNORECASE),
    priority=25
), {
    "品名": "工资",
    "付款详情": "员工工资发放",
})
```

### 3. Combined Description + Amount Rules

Rules can match both description patterns AND amount ranges:

```python
# Small service fees (<$50)
(TransactionMatchRule(
    description_pattern=re.compile(r'SERVICE|FEE', re.IGNORECASE),
    amount_pattern=(0.01, 50.0),
    priority=15
), {
    "付款详情": "小额银行服务费",
    "单据号": False,
})

# Large service fees (>$50) - need documentation
(TransactionMatchRule(
    description_pattern=re.compile(r'SERVICE|FEE', re.IGNORECASE),
    amount_pattern=(50.0, float('inf')),
    priority=15
), {
    "付款详情": "大额银行服务费",
    "单据号": True,
    "附件": True,
})
```

## Usage Examples

### Basic Classification (Backward Compatible)

```python
from configs.bank_desc import BankDescriptionConfig

# Simple description-only classification
result = BankDescriptionConfig.get_transaction_info("UBER HOLDINGS")
print(result['付款详情'])  # "Uber外卖佣金"
```

### Enhanced Classification with Amount

```python
# Large UBER transaction
result = BankDescriptionConfig.get_transaction_info("UBER HOLDINGS", 2500.0)
print(result['付款详情'])  # "Uber外卖大额进账"
print(result['单据号'])     # True (requires documentation)

# Small UBER transaction  
result = BankDescriptionConfig.get_transaction_info("UBER HOLDINGS", 150.0)
print(result['付款详情'])  # "Uber外卖佣金"
print(result['单据号'])     # False (no extra documentation)
```

### Processing in Bank Transaction Script

The bank processing script now automatically passes amount information:

```python
# In process_bank_transactions.py
transaction_amount = None
if credit and isinstance(credit, (int, float)) and credit > 0:
    transaction_amount = float(credit)
elif debit and isinstance(debit, (int, float)) and debit > 0:
    transaction_amount = -float(debit)
    
classification = BankDescriptionConfig.get_transaction_info(
    combined_text, transaction_amount)
```

## Adding New Rules

### 1. Simple String Match Rule

```python
# Add to BANK_TRANSACTION_RULES list in configs/bank_transaction_rules.py
(TransactionMatchRule(
    description_pattern="NEW PATTERN",
    priority=50
), {
    "品名": "新分类",
    "付款详情": "新描述",
    "单据号": False,
    "附件": False,
    "是否登记线下付款表": False,
    "是否登记支票使用表": False,
})
```

### 2. Regex Pattern Rule

```python
(TransactionMatchRule(
    description_pattern=re.compile(r'\bMY\s+PATTERN\b', re.IGNORECASE),
    priority=30
), {
    "品名": "正则分类",
    "付款详情": "正则匹配描述",
})
```

### 3. Amount-Based Rule

```python
# Exact amount match
(TransactionMatchRule(
    description_pattern="MONTHLY FEE",
    amount_pattern=99.99,  # Exact $99.99
    priority=20
), {
    "品名": "固定费用",
    "付款详情": "每月固定费用",
})

# Amount range match
(TransactionMatchRule(
    description_pattern="VARIABLE FEE",
    amount_pattern=(100.0, 500.0),  # Between $100-$500
    priority=20
), {
    "品名": "变动费用",
    "付款详情": "变动金额费用",
})
```

### 4. Dynamic Rule Addition

```python
# Add rules at runtime
new_rule = TransactionMatchRule(
    description_pattern=re.compile(r'DYNAMIC\s+PATTERN', re.IGNORECASE),
    amount_pattern=(1000.0, float('inf')),
    priority=5
)

classification = {
    "品名": "动态分类",
    "付款详情": "动态添加的规则",
    "单据号": True,
}

BankDescriptionConfig.add_rule(new_rule, classification)
```

## Rule Evaluation Order

Rules are evaluated in the order they appear in the list (first match wins):

1. **Most Specific**: Exact regex patterns (BMO internal transfers, SNAPPY patterns)
2. **Amount-based**: Rules that match both description and amount
3. **Regex patterns**: Flexible patterns for similar transaction types
4. **Exact strings**: Direct string matches for specific patterns  
5. **Partial matches**: Generic patterns that catch common terms

This simple ordering ensures predictable behavior - the first rule that matches will be used.

## Migration Guide

### For Existing Patterns

All existing patterns in `bank_desc.py` have been converted and are fully compatible. No changes needed for basic usage.

### For New Features

To take advantage of amount-based classification:

1. **Update calling code** to pass amount information:
   ```python
   # Old way
   result = BankDescriptionConfig.get_transaction_info(description)
   
   # New way
   result = BankDescriptionConfigNew.get_transaction_info(description, amount)
   ```

2. **Add amount-specific rules** for transactions that need different handling based on size

3. **Use regex patterns** for more flexible matching

## Testing

Run the comprehensive test suite to verify the system:

```bash
# Run the complete test suite for bank classification
python -m unittest tests.test_bank_desc_classification -v

# Or run all tests in the tests directory
python -m unittest discover tests -v

# Quick functionality test
python -c "from configs.bank_desc import BankDescriptionConfig; print('System works!')"
```

The test suite includes:
- Amount-based classification tests
- Regex pattern matching tests  
- Rule ordering validation
- Edge case handling
- Integration testing with bank processing
- Dynamic rule addition testing

## Debugging

### Get All Matching Rules

```python
# See which rules match a description
matching_rules = BankDescriptionConfig.get_rules_for_description("UBER HOLDINGS")
for i, (rule, classification) in enumerate(matching_rules):
    print(f"Rule {i+1}: {classification['付款详情']}")
```

### Rule Evaluation Order

Rules are evaluated in list order. The first matching rule wins. Use this to debug why a transaction gets a particular classification.

## Benefits

1. **More Accurate Classification**: Amount-based rules provide context-aware classification
2. **Flexible Matching**: Regex patterns handle variations in transaction descriptions
3. **Automated Documentation**: System automatically determines when transactions need documentation
4. **Maintainable**: Simple list ordering makes it easy to understand and modify rules
5. **Backward Compatible**: All existing functionality preserved

## Future Enhancements

The new system is designed to be extensible. Future additions could include:

- **Date-based rules**: Different classification based on time of year
- **Account-based rules**: Different handling per bank account
- **Machine learning integration**: AI-powered classification for unknown patterns
- **Statistical analysis**: Automatic detection of patterns in transaction data