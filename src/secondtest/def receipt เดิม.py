def generate_receipt_pdf(self, order_id):
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
            order_info = cursor.fetchone()
            if not order_info:
                QMessageBox.warning(self, "Error", f"Order {order_id} not found.")
                conn.close()
                return

            cursor.execute("""
                SELECT oi.product_id, p.name, oi.unit_price, oi.quantity
                FROM order_items oi
                LEFT JOIN product p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (order_id,))
            items = cursor.fetchall()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Could not fetch order data: {e}")
            return

        try:
            if not os.path.exists(PDF_OUTPUT_DIR):
                os.makedirs(PDF_OUTPUT_DIR)

            pdf_filename = os.path.join(PDF_OUTPUT_DIR, f"Receipt_{order_info['user_id']}_{order_id}.pdf")
            pdf_filename = os.path.abspath(pdf_filename)

            c = canvas.Canvas(pdf_filename, pagesize=A4)
            width, height = A4

            # --- HEADER ---
            LOGO_X, LOGO_Y = 15 * mm, height - 60 * mm
            LOGO_W, LOGO_H = 50 * mm, 40 * mm
            if os.path.exists(LOGO_PATH):
                try:
                    c.drawImage(LOGO_PATH, LOGO_X, LOGO_Y, width=LOGO_W, height=LOGO_H, preserveAspectRatio=True,
                                mask='auto')
                except:
                    pass

            c.setFont(self.main_pdf_font, 14)
            text_y = height - 55 * mm
            for line in ["ที่อยู่ร้านค้า :", "หอพักนักศึกษาชายที่ 10 มหาวิทยาลัยขอนแก่น",
                         "ตำบล ศิลา อำเภอเมืองขอนแก่น จังหวัด ขอนแก่น 40000",
                         "เลขประจำตัวผู้เสียภาษี 3101103733"]:
                c.drawString(20 * mm, text_y, line)
                text_y -= 6 * mm

            c.setFont("Helvetica-Bold", 20)
            c.drawCentredString(width / 2.0, height - 20 * mm, f"ORDER ID # {order_info['order_id']}")

            c.setFont("Helvetica", 7)
            c.drawString(135 * mm, height - 55 * mm, "CUSTOMER :")
            c.drawString(135 * mm, height - 65 * mm, "ORDER DATE :")

            c.setFont(self.main_pdf_font, 14)
            c.drawString(155 * mm, height - 55 * mm, str(order_info['user_id']))
            c.drawString(155 * mm, height - 65 * mm, str(order_info['order_date']))

            # --- TABLE ---
            table_data = [['ID', 'ITEM', 'UNIT PRICE', 'QUANTITY', 'AMOUNT']]
            for idx, item in enumerate(items, 1):
                u_price = item['unit_price']
                qty = item['quantity']
                amount = u_price * qty
                table_data.append([
                    str(idx),
                    item['name'] if item['name'] else "Unknown Item",
                    f"{u_price:,.2f} THB",
                    str(qty),
                    f"{amount:,.2f} THB"
                ])

            table = Table(table_data, colWidths=[10 * mm, 70 * mm, 35 * mm, 20 * mm, 35 * mm])
            table.setStyle(TableStyle([
                ('FONT', (0, 0), (-1, -1), self.main_pdf_font, 12),
                ('ALIGN', (1, 1), (-1, 0), 'LEFT'),                 # หัวตาราง: ชิดซ้าย
                ('ALIGN', (5, 1), (-1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LINEABOVE', (0, 0), (-1, 0), 1, colors.black),
                ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),
                ('WORDWRAP', (1, 1), (1, -1), True),
            ]))

            available_width = width - 40 * mm
            _, table_height = table.wrap(available_width, height)
            table_top_y = height - 80 * mm
            table_y = table_top_y - table_height
            table.drawOn(c, 20 * mm, table_y)

            # --- FOOTER ---
            y_footer = table_y - 20 * mm
            c.setLineWidth(0.5)
            c.line(20 * mm, y_footer + 5 * mm, width - 20 * mm, y_footer + 5 * mm)

            c.setFont(self.main_pdf_font, 14)
            right_x = width - 25 * mm

            c.drawRightString(right_x - 40 * mm, y_footer - 5 * mm, "Subtotal :")
            c.drawRightString(right_x, y_footer - 5 * mm, f"{order_info['subtotal']:,.2f} THB")

            c.drawRightString(right_x - 40 * mm, y_footer - 12 * mm, "Shipping :")
            c.drawRightString(right_x, y_footer - 12 * mm, f"{order_info['shipping_fee']:,.2f} THB")

            c.drawRightString(right_x - 40 * mm, y_footer - 19 * mm, "VAT 7% :")
            c.drawRightString(right_x, y_footer - 19 * mm, f"{order_info['vat']:,.2f} THB")

            c.line(width - 80 * mm, y_footer - 24 * mm, width - 20 * mm, y_footer - 24 * mm)
            c.setFont("Helvetica", 16)
            c.drawRightString(right_x - 40 * mm, y_footer - 32 * mm, "Total :")
            c.drawRightString(right_x, y_footer - 32 * mm, f"{order_info['total']:,.2f} THB")

            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(width / 2.0, 30 * mm, "Thank bro, you are my hero!")

            c.save()

            # สั่งเปิดไฟล์ทันที
            if os.name == 'nt':  # สำหรับ Windows
                os.startfile(pdf_filename)
            else:  # สำหรับ macOS หรือ Linux
                import subprocess
                opener = 'open' if sys.platform == 'darwin' else 'xdg-open'
                subprocess.call([opener, pdf_filename])

        except Exception as e:
            QMessageBox.critical(self, "PDF Error", f"Could not create receipt PDF: {e}")
            import traceback
            traceback.print_exc()