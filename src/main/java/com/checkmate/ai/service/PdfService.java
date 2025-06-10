package com.checkmate.ai.service;

import com.checkmate.ai.dto.StudentResponseDto;
import com.checkmate.ai.entity.*;
import com.checkmate.ai.repository.jpa.ExamRepository;
import com.checkmate.ai.repository.jpa.StudentResponseRepository;
import com.itextpdf.io.font.FontProgram;
import com.itextpdf.io.font.FontProgramFactory;
import com.itextpdf.io.font.PdfEncodings;
import com.itextpdf.kernel.colors.ColorConstants;
import com.itextpdf.kernel.font.PdfFont;
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfWriter;
import com.itextpdf.layout.properties.UnitValue;
import com.itextpdf.layout.Document;
import com.itextpdf.kernel.colors.DeviceRgb;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.Resource;
import org.springframework.core.io.ResourceLoader;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import com.itextpdf.layout.element.Cell;
import com.itextpdf.layout.element.Paragraph;
import com.itextpdf.layout.element.Table;
import com.itextpdf.layout.properties.TextAlignment;
import com.itextpdf.kernel.font.PdfFontFactory;
import com.itextpdf.io.font.constants.StandardFonts;
import org.springframework.web.client.RestTemplate;

import javax.imageio.ImageIO;
import javax.imageio.ImageWriter;
import java.awt.image.BufferedImage;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.zip.ZipEntry;
import java.util.zip.ZipOutputStream;


@Service
@RequiredArgsConstructor
public class PdfService {


    @Value("${flask.server.url}")
    private String flaskReportUrl;

    @Autowired
    @Qualifier("webApplicationContext")
    private ResourceLoader resourceLoader;

    @Autowired
    private RestTemplate restTemplate;


    @Autowired
    private  ExamRepository examRepository;

    @Autowired
    private StudentResponseRepository studentResponseRepository;


//    @Value("${file.image-dir}")
//    private String imageDir;

// ...


    public void saveZipFile(byte[] zipData, String fileName) throws IOException {
        Path outputPath = Paths.get("/app/report/", fileName);  // 예: /files/ 디렉토리
        Files.write(outputPath, zipData);
    }



    public List<byte[]> fetchImagesFromFlask(String studentId, String subject) {
        RestTemplate restTemplate = new RestTemplate();

        String url = flaskReportUrl+ "/get-student-image";

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, String> body = new HashMap<>();
        body.put("student_id", studentId);
        body.put("subject", subject);


        HttpEntity<Map<String, String>> entity = new HttpEntity<>(body, headers);

        ResponseEntity<byte[]> response = restTemplate.exchange(
                url,
                HttpMethod.POST,
                entity,
                byte[].class
        );

        if (response.getStatusCode() == HttpStatus.OK) {
            return List.of(response.getBody());
        } else {
            throw new RuntimeException("이미지를 불러오지 못했습니다");
        }
    }


    public byte[] createZipWithPdfAndImages(String subject, Student student, byte[] pdfBytes, List<byte[]> imageBytesList) throws IOException {
        try (ByteArrayOutputStream baos = new ByteArrayOutputStream();
             ZipOutputStream zos = new ZipOutputStream(baos)) {

            // 1. PDF 파일 추가 (예: 수학_20230002_김철수.pdf)
            String sanitizedSubject = subject.replaceAll("[^a-zA-Z0-9가-힣_]", "_"); // 혹시 모를 특수문자 처리
            String sanitizedName = student.getStudentName().replaceAll("\\s+", ""); // 이름 공백 제거
            String pdfFileName = String.format("%s_%s_%s.pdf", sanitizedSubject, student.getStudentId(), sanitizedName);

            ZipEntry pdfEntry = new ZipEntry(pdfFileName);
            zos.putNextEntry(pdfEntry);
            zos.write(pdfBytes);
            zos.closeEntry();

            // 2. 이미지 파일 추가
            for (int i = 0; i < imageBytesList.size(); i++) {
                byte[] imageBytes = imageBytesList.get(i);
                String extension = detectImageExtension(imageBytes); // 확장자 감지
                String imageFileName = String.format("image_%d.%s", i + 1, extension);
                ZipEntry imageEntry = new ZipEntry(imageFileName);
                zos.putNextEntry(imageEntry);
                zos.write(imageBytes);
                zos.closeEntry();
            }

            zos.finish();
            return baos.toByteArray();
        }
    }



    private String detectImageExtension(byte[] imageBytes) {
        try (InputStream is = new ByteArrayInputStream(imageBytes)) {
            BufferedImage image = ImageIO.read(is);
            if (image == null) return "bin"; // 이미지가 아닐 경우
            Iterator<ImageWriter> writers = ImageIO.getImageWritersByFormatName("png");
            if (writers.hasNext()) return "png"; // 우선순위: PNG
            writers = ImageIO.getImageWritersByFormatName("jpg");
            if (writers.hasNext()) return "jpg";
            return "img"; // 기본 fallback
        } catch (IOException e) {
            return "img";
        }
    }


    public byte[] generatePdf(String subject, Student student) {
        ByteArrayOutputStream out = new ByteArrayOutputStream();

        try (PdfWriter writer = new PdfWriter(out);
             PdfDocument pdf = new PdfDocument(writer);
             Document document = new Document(pdf)) {

            // 폰트 읽기
            Resource fontResource = resourceLoader.getResource("classpath:/static/fonts/NanumGothic.ttf");

            byte[] fontBytes;
            try (InputStream is = fontResource.getInputStream()) {
                fontBytes = is.readAllBytes();
            }

            // FontProgram 생성
            FontProgram fontProgram = FontProgramFactory.createFont(fontBytes);

            // PdfFont 생성 (createFont(FontProgram)만 존재함)
            PdfFont font = PdfFontFactory.createFont(fontProgram, PdfEncodings.IDENTITY_H);


            System.out.println(font);
            document.setFont(font);

            document.add(new Paragraph(subject + " - " + student.getStudentId() + " 시험 리포트")
                    .setFontSize(16)
                    .setTextAlignment(TextAlignment.CENTER)
                    .setMarginBottom(20));

            Exam exam = examRepository.findBySubject(subject)
                    .orElseThrow(() -> new RuntimeException("해당 과목 시험 정보가 없습니다."));

            // studentId 대신 student 객체를 넘겨야 함
            StudentResponse response = studentResponseRepository.findByStudentAndSubject(student, subject)
                    .orElseThrow(() -> new RuntimeException("해당 학생의 응답이 존재하지 않습니다."));

            // 테이블 생성
            Table table = new Table(UnitValue.createPercentArray(new float[]{2, 3, 3, 2}))
                    .useAllAvailableWidth();

            // 컬럼 헤더 스타일
            String[] headers = {"질문 번호.", "학생 응답", "정답", "문항 점수"};
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
                        .filter(q -> q.getQuestionNumber() == answer.getQuestionNumber()
                                && q.getSubQuestionNumber() == answer.getSubQuestionNumber())
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
            document.add(new Paragraph("\n총점: " + response.getTotalScore())
                    .setTextAlignment(TextAlignment.RIGHT)
                    .setFontSize(24)
                    .setBold());

            document.add(table);

        } catch (Exception e) {
            e.printStackTrace();
        }

        return out.toByteArray();
    }


    public ResponseEntity<ByteArrayResource> downloadSubjectReportPdf(String subject, List<StudentResponse> responses) {


        // 3. Flask로 POST 요청 보낼 JSON 구성
        Map<String, Object> requestBody = new HashMap<>();
        requestBody.put("subject", subject);
        requestBody.put("responses", responses);

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.valueOf("application/json; charset=UTF-8"));  // 인코딩 명시
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.setAccept(List.of(MediaType.APPLICATION_PDF));

        HttpEntity<Map<String, Object>> requestEntity = new HttpEntity<>(requestBody, headers);

        // 4. POST 요청 전송
        ResponseEntity<byte[]> response = restTemplate.exchange(
                flaskReportUrl+"/generate-report",  // 예: http://flask-server:5000/generate-report
                HttpMethod.POST,
                requestEntity,
                byte[].class
        );

        if (response.getStatusCode().is2xxSuccessful()) {
            ByteArrayResource resource = new ByteArrayResource(response.getBody());

            HttpHeaders responseHeaders = new HttpHeaders();

            responseHeaders.setContentType(MediaType.APPLICATION_PDF);
            responseHeaders.setContentDisposition(ContentDisposition
                    .attachment()
                    .filename(subject + "_report.pdf")
                    .build());

            return new ResponseEntity<>(resource, responseHeaders, HttpStatus.OK);
        } else {
            return new ResponseEntity<>(HttpStatus.BAD_GATEWAY);
        }
    }
}
