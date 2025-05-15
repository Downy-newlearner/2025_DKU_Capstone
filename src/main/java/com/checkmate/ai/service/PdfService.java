package com.checkmate.ai.service;

import com.checkmate.ai.entity.Exam;
import com.checkmate.ai.entity.ExamResponse;
import com.checkmate.ai.entity.Question;
import com.checkmate.ai.entity.StudentResponse;
import com.checkmate.ai.repository.ExamRepository;
import com.checkmate.ai.repository.StudentResponseRepository;
import com.itextpdf.kernel.colors.ColorConstants;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.layout.properties.UnitValue;
import com.itextpdf.layout.Document;
import com.itextpdf.kernel.colors.DeviceRgb;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.itextpdf.layout.element.Cell;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.element.Table;
import com.itextpdf.layout.properties.TextAlignment;
import com.itextpdf.kernel.font.PdfFontFactory;
import com.itextpdf.io.font.constants.StandardFonts;
import java.io.ByteArrayOutputStream;
import java.util.List;


@Service
@RequiredArgsConstructor
public class PdfService {

    @Autowired
    private  ExamRepository examRepository;

    @Autowired
    private StudentResponseRepository studentResponseRepository;


// ...

    public byte[] generatePdf(String subject, String studentId) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();

        try (PdfWriter writer = new PdfWriter(out);
             PdfDocument pdf = new PdfDocument(writer);
             Document document = new Document(pdf)) {

            // 제목
            document.add(new Paragraph(subject + " - " + studentId + " Exam Report")
                    .setFont(PdfFontFactory.createFont(StandardFonts.HELVETICA_BOLD))
                    .setFontSize(16)
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(20));

            // 시험 정보 조회
            Exam exam = examRepository.findBySubject(subject)
                    .orElseThrow(() -> new RuntimeException("해당 과목 시험 정보가 없습니다."));

            // 학생 응답 조회
            StudentResponse response = studentResponseRepository.findByStudentIdAndSubject(studentId, subject)
                    .orElseThrow(() -> new RuntimeException("해당 학생의 응답이 존재하지 않습니다."));

            // 테이블 생성
            Table table = new Table(UnitValue.createPercentArray(new float[]{2, 3, 3, 2}))
                    .useAllAvailableWidth();

            // 컬럼 헤더 스타일
            String[] headers = {"No.", "Student Answer", "Correct Answer", "Allocated Point"};
            for (String header : headers) {
                Cell headerCell = new Cell()
                        .add(new Paragraph(header).setBold())
                        .setBackgroundColor(ColorConstants.LIGHT_GRAY)
                        .setTextAlignment(TextAlignment.CENTER);
                table.addHeaderCell(headerCell);
            }

            // 색상 정의
            com.itextpdf.kernel.colors.Color lightBlue = new DeviceRgb(173, 216, 230); // 하늘색
            com.itextpdf.kernel.colors.Color softRed = new DeviceRgb(255, 204, 203);   // 연분홍

            for (ExamResponse answer : response.getAnswers()) {
                Question question = exam.getQuestions().stream()
                        .filter(q -> q.getQuestion_number() == answer.getQuestionNumber()
                                && q.getSub_question_number() == answer.getSubQuestionNumber())
                        .findFirst()
                        .orElse(null);

                if (question != null) {
                    String questionKey = answer.getQuestionNumber() + "-" + answer.getSubQuestionNumber();

                    // 맞았으면 하늘색, 틀렸으면 연분홍
                    com.itextpdf.kernel.colors.Color bgColor = answer.isCorrect() ? lightBlue : softRed;

                    table.addCell(new Cell().add(new Paragraph(questionKey)).setBackgroundColor(bgColor));
                    table.addCell(new Cell().add(new Paragraph(answer.getStudentAnswer())).setBackgroundColor(bgColor));
                    table.addCell(new Cell().add(new Paragraph(question.getAnswer())).setBackgroundColor(bgColor));
                    table.addCell(new Cell().add(new Paragraph(String.valueOf(answer.getScore()))).setBackgroundColor(bgColor));
                }
            }

            // 전체 점수 요약
            document.add(new Paragraph("\nTotal Score: " + response.getTotalScore())
                    .setTextAlignment(TextAlignment.RIGHT)
                    .setFontSize(12)
                    .setBold());

            document.add(table);

        } catch (Exception e) {
            e.printStackTrace();
        }

        return out.toByteArray();
    }

}
