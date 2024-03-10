class TextExtractor:
    @staticmethod
    def is_inside(paragraph_block, text_block):
        allowable_error_pixel = 10 if paragraph_block.width > 300 else 3
        return (
            text_block.block.x_1 >= paragraph_block.block.x_1 - allowable_error_pixel and
            text_block.block.y_1 >= paragraph_block.block.y_1 - allowable_error_pixel and
            text_block.block.x_2 <= paragraph_block.block.x_2 + allowable_error_pixel and
            text_block.block.y_2 <= paragraph_block.block.y_2 + allowable_error_pixel
        )
    
    @staticmethod
    def text_blocks_to_words(text_blocks, coalesce_threshold=1):
        if not text_blocks:
            return []
        
        words = [text_blocks[0].text]
        prev_x_2 = text_blocks[0].block.x_2
        
        for block in text_blocks[1:]:
            gap_x = block.block.x_1 - prev_x_2
            if gap_x > coalesce_threshold:
                words.append(block.text)
            else:
                words[-1] += block.text
            prev_x_2 = block.block.x_2
        
        return words
