    def _get_company_name_from_code(self, stock_code: str) -> str:
        """
        根据股票代码获取公司名称
        
        Args:
            stock_code: 股票代码
            
        Returns:
            str: 公司名称，如果无法获取则返回空字符串
        """
        # 简单的映射表（常见股票）
        stock_name_map = {
            '09618': '京东集团',
            '9618': '京东集团',
            'JD': '京东',
            '00700': '腾讯控股',
            '0700': '腾讯控股',
            'BABA': '阿里巴巴',
            '09988': '阿里巴巴',
            'AAPL': '苹果',
            'TSLA': '特斯拉',
            'NVDA': '英伟达',
            '000001': '平安银行',
            '600519': '贵州茅台',
        }
        
        # 标准化代码
        clean_code = stock_code.replace('.HK', '').replace('.SH', '').replace('.SZ', '')
        
        # 查找映射
        company_name = stock_name_map.get(clean_code, '')
        
        if company_name:
            logger.debug(f"[统一新闻工具] 股票代码 {stock_code} 映射到公司名称: {company_name}")
        else:
            logger.debug(f"[统一新闻工具] 股票代码 {stock_code} 未找到公司名称映射")
        
        return company_name
