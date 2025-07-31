#!/usr/bin/env python3
"""
Unit tests for the bank description classification system.
Tests the enhanced tuple-based classification with regex and amount matching.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from configs.bank_desc import BankDescriptionConfig


class TestBankDescriptionClassification(unittest.TestCase):
    """Test cases for bank transaction classification system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.classifier = BankDescriptionConfig
    
    def test_exact_amount_matching(self):
        """Test exact amount matching for recurring transactions"""
        # Test with exact amount match (if we had a rule defined)
        # For now, test that regular UBER transactions work normally
        regular_result = self.classifier.get_transaction_info("UBER EATS PAYMENT", 150.0)
        self.assertEqual(regular_result['付款详情'], "Uber外卖佣金")
        self.assertFalse(regular_result['单据号'])
        self.assertFalse(regular_result['附件'])
        
        # Another UBER transaction with different amount should also match general rule
        another_result = self.classifier.get_transaction_info("UBER HOLDINGS", 2500.0)
        self.assertEqual(another_result['付款详情'], "Uber外卖佣金")  # Should use general rule
        self.assertFalse(another_result['单据号'])
        self.assertFalse(another_result['附件'])
    
    def test_transaction_type_matching(self):
        """Test credit/debit transaction type matching"""
        # Test built-in service charge rule (debit only)
        service_result_debit = self.classifier.get_transaction_info("SERVICE CHARGE", 25.0, 'debit')
        self.assertEqual(service_result_debit['付款详情'], "银行服务费")
        
        # Same description with credit type should NOT match the debit-only rule
        service_result_credit = self.classifier.get_transaction_info("SERVICE CHARGE", 25.0, 'credit')
        self.assertNotEqual(service_result_credit['付款详情'], "银行服务费")
        
        # Test exact BMO plan fee matching
        plan_fee_debit = self.classifier.get_transaction_info("Service Charge", 120.0, 'debit')
        self.assertEqual(plan_fee_debit['付款详情'], "BMO月度账户费")
        
        # Test BMO plan fee rebate (credit)
        plan_fee_credit = self.classifier.get_transaction_info("Service Charge / Correction", 120.0, 'credit')
        self.assertEqual(plan_fee_credit['付款详情'], "BMO账户费退款")
        
        # Test that we can add a rule with transaction type and it works
        from configs.bank_transaction_rules import TransactionMatchRule
        
        # Add a test rule for credit transactions
        credit_rule = TransactionMatchRule(
            description_pattern="TEST CREDIT",
            transaction_type='credit'
        )
        
        credit_classification = {
            "品名": "测试收入",
            "付款详情": "测试信用交易",
            "单据号": False,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        }
        
        self.classifier.add_rule(credit_rule, credit_classification)
        
        # Test credit transaction type
        result = self.classifier.get_transaction_info("TEST CREDIT PAYMENT", 100.0, 'credit')
        self.assertEqual(result['付款详情'], "测试信用交易")
        
        # Test that debit transaction type doesn't match
        debit_result = self.classifier.get_transaction_info("TEST CREDIT PAYMENT", 100.0, 'debit')
        self.assertNotEqual(debit_result['付款详情'], "测试信用交易")  # Should not match
    
    def test_bmo_internal_transfer_regex(self):
        """Test BMO internal transfer pattern matching"""
        test_patterns = [
            "0782-1931-699 3587",
            "0782-1931-680 3587", 
            "0782-1931-123 4567"
        ]
        
        for pattern in test_patterns:
            result = self.classifier.get_transaction_info(pattern)
            self.assertEqual(result['付款详情'], "BMO内部转款")
            self.assertEqual(result['品名'], "内部转款")
            self.assertFalse(result['是否登记线下付款表'])
    
    def test_real_data_patterns(self):
        """Test patterns from real transaction data analysis"""
        # IOT PAY - Most frequent pattern (194x)
        result = self.classifier.get_transaction_info("Direct Deposit IOT PAY MSP/DIV", 4903.61, 'credit')
        self.assertEqual(result['付款详情'], "微信支付宝进账")
        self.assertEqual(result['品名'], "收入进账")
        
        # UBER HOLDINGS - 44x occurrences
        result = self.classifier.get_transaction_info("Direct Deposit UBER HOLDINGS C MSP/DIV", 1199.22, 'credit')
        self.assertEqual(result['付款详情'], "Uber外卖佣金")
        
        # FANTUAN - 55x occurrences  
        result = self.classifier.get_transaction_info("Direct Deposit FANTUAN MSP/DIV", 854.33, 'credit')
        self.assertEqual(result['付款详情'], "饭团外卖佣金")
        
        # BR. patterns - Cash deposits
        result = self.classifier.get_transaction_info("Branch Credit BR. 3833", 195.0, 'credit')
        self.assertEqual(result['付款详情'], "现金收入")
        self.assertTrue(result['单据号'])
        
        # DP patterns - Clover deposits
        result = self.classifier.get_transaction_info("Direct Deposit DP22048140016 MSP/DIV", 123080.94, 'credit')
        self.assertEqual(result['付款详情'], "Clover刷卡进账")
    
    def test_payroll_regex_patterns(self):
        """Test various payroll description patterns"""
        # Test real payroll pattern from data analysis
        result = self.classifier.get_transaction_info("Preauthorized Debit / Correction PAYROLL TBJ0086 BUS/ENT", 1000.0, 'debit')
        self.assertEqual(result['付款详情'], "员工工资发放")
        self.assertEqual(result['品名'], "工资")
        self.assertTrue(result['附件'])
        self.assertTrue(result['是否登记线下付款表'])
        
        # Test another real pattern
        result = self.classifier.get_transaction_info("Preauthorized Debit / Correction PAYROLL 3XF0086 BUS/ENT", 2000.0, 'debit')
        self.assertEqual(result['付款详情'], "员工工资发放")
    
    def test_credit_card_patterns(self):
        """Test credit card transaction patterns"""
        # These patterns should match credit card rules (avoid words that match SERVICE|FEE regex)
        credit_card_patterns = [
            "CREDIT CARD PAYMENT",
            "VISA TRANSACTION",
            "MASTERCARD PAYMENT", 
            "AMEX TRANSACTION"
        ]
        
        for pattern in credit_card_patterns:
            result = self.classifier.get_transaction_info(pattern)
            self.assertEqual(result['付款详情'], "信用卡相关交易")
            self.assertEqual(result['品名'], "信用卡还款")
            self.assertTrue(result['是否登记线下付款表'])
    
    def test_pattern_conflicts(self):
        """Test how pattern matching works with overlapping patterns"""
        # MASTERCARD FEE should match SERVICE|FEE pattern (comes first in list)
        # Since we removed amount-based service fee rules, it should match generic pattern
        result = self.classifier.get_transaction_info("MASTERCARD FEE")
        # Should match credit card pattern now since SERVICE|FEE amount rules are removed
        self.assertEqual(result['付款详情'], "信用卡相关交易")
        
        # MASTERCARD PAYMENT should also match credit card pattern
        result = self.classifier.get_transaction_info("MASTERCARD PAYMENT")
        self.assertEqual(result['付款详情'], "信用卡相关交易")
    
    def test_exact_recurring_amounts(self):
        """Test exact recurring amount patterns from real data"""
        # BMO Plan Fee - exact $120.00 debit
        result = self.classifier.get_transaction_info("Service Charge", 120.0, 'debit')
        self.assertEqual(result['付款详情'], "BMO月度账户费")
        self.assertEqual(result['品名'], "服务费")
        
        # BMO Plan Fee Rebate - exact $120.00 credit
        result = self.classifier.get_transaction_info("Service Charge / Correction", 120.0, 'credit')
        self.assertEqual(result['付款详情'], "BMO账户费退款")
        self.assertEqual(result['品名'], "回冲")
        
        # ACURA Finance - exact $396.37 debit
        result = self.classifier.get_transaction_info("Preauthorized Debit / Correction", 396.37, 'debit')
        self.assertEqual(result['付款详情'], "ACURA汽车租赁费")
        self.assertEqual(result['品名'], "租赁费")
        
        # ICBC Insurance from real data
        result = self.classifier.get_transaction_info("Preauthorized Debit / Correction ICBC INS/ASS", 192.95, 'debit')
        self.assertEqual(result['付款详情'], "ICBC保险费")
        self.assertEqual(result['品名'], "保险费")
    
    def test_fallback_patterns(self):
        """Test that fallback patterns work correctly"""
        # Generic UBER match (fallback pattern)
        result = self.classifier.get_transaction_info("UBER EATS", 150.0)
        self.assertEqual(result['付款详情'], "Uber外卖佣金")
        
        # Generic DEPOSIT match (fallback pattern)
        result = self.classifier.get_transaction_info("CASH DEPOSIT", 100.0, 'credit')
        self.assertEqual(result['付款详情'], "银行现金存款")
        
        # Generic TRANSFER match (fallback pattern)
        result = self.classifier.get_transaction_info("WIRE TRANSFER")
        self.assertEqual(result['付款详情'], "账户转账")
        
        # Interest patterns
        result = self.classifier.get_transaction_info("ACCOUNT INTEREST")
        self.assertEqual(result['付款详情'], "利息收入")
    
    def test_rule_ordering(self):
        """Test that rule ordering works correctly (first match wins)"""
        # BMO pattern should match before generic transfer (BMO comes first in list)
        result = self.classifier.get_transaction_info("0782-1931-699 3587 TRANSFER")
        self.assertEqual(result['付款详情'], "BMO内部转款")  # Should match BMO pattern, not generic transfer
        
        # Regular UBER should match the general UBER rule
        result = self.classifier.get_transaction_info("UBER HOLDINGS", 1500.0)
        self.assertEqual(result['付款详情'], "Uber外卖佣金")  # Should match general UBER rule
    
    def test_unknown_transactions(self):
        """Test handling of unknown transaction patterns"""
        unknown_patterns = [
            "UNKNOWN MERCHANT",
            "RANDOM PAYMENT", 
            "MYSTERY TRANSACTION"
        ]
        
        for pattern in unknown_patterns:
            result = self.classifier.get_transaction_info(pattern)
            self.assertEqual(result['付款详情'], "需要手动分类")
            self.assertEqual(result['品名'], "未分类交易")
            self.assertFalse(result['单据号'])
            self.assertFalse(result['附件'])
            self.assertFalse(result['是否登记线下付款表'])
            self.assertFalse(result['是否登记支票使用表'])
    
    def test_empty_description(self):
        """Test handling of empty or None descriptions"""
        result = self.classifier.get_transaction_info("")
        self.assertEqual(result['付款详情'], "需要手动分类")
        
        result = self.classifier.get_transaction_info(None)
        self.assertEqual(result['付款详情'], "需要手动分类")
    
    def test_get_rules_for_description(self):
        """Test the debugging method for getting matching rules"""
        matching_rules = self.classifier.get_rules_for_description("UBER HOLDINGS")
        self.assertGreater(len(matching_rules), 0)
        
        # Should have both specific and general UBER rules
        rule_details = [rule[1]['付款详情'] for rule in matching_rules]
        self.assertIn("Uber外卖佣金", rule_details)
    
    def test_add_rule_functionality(self):
        """Test adding new rules dynamically"""
        from configs.bank_transaction_rules import TransactionMatchRule
        
        # Add a test rule
        test_rule = TransactionMatchRule(
            description_pattern="TEST PATTERN"
        )
        
        test_classification = {
            "品名": "测试分类",
            "付款详情": "测试描述",
            "单据号": True,
            "附件": False,
            "是否登记线下付款表": False,
            "是否登记支票使用表": False,
        }
        
        # Add the rule
        self.classifier.add_rule(test_rule, test_classification)
        
        # Test that it works
        result = self.classifier.get_transaction_info("TEST PATTERN TRANSACTION")
        self.assertEqual(result['付款详情'], "测试描述")
        self.assertEqual(result['品名'], "测试分类")


class TestIntegrationWithBankProcessing(unittest.TestCase):
    """Integration tests to ensure compatibility with bank processing script"""
    
    def test_amount_parameter_handling(self):
        """Test that amount parameter is handled correctly"""
        classifier = BankDescriptionConfig
        
        # Test with positive amount (credit)
        result = classifier.get_transaction_info("SERVICE CHARGE", 25.0)
        self.assertIsInstance(result, dict)
        
        # Test with negative amount (debit)  
        result = classifier.get_transaction_info("PAYROLL", -2000.0)
        self.assertIsInstance(result, dict)
        
        # Test with None amount
        result = classifier.get_transaction_info("DEPOSIT", None)
        self.assertIsInstance(result, dict)
    
    def test_required_fields_present(self):
        """Test that all required fields are present in results"""
        required_fields = [
            '品名', '付款详情', '单据号', '附件', 
            '是否登记线下付款表', '是否登记支票使用表'
        ]
        
        result = BankDescriptionConfig.get_transaction_info("TEST TRANSACTION")
        
        for field in required_fields:
            self.assertIn(field, result)
            self.assertIsNotNone(result[field])


if __name__ == '__main__':
    # Set encoding for Windows console
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    
    unittest.main(verbosity=2)