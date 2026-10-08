package com.korpodrony.servlet.admin;

import com.korpodrony.freemarker.TemplateProvider;
import com.korpodrony.services.UploadService;
import freemarker.template.Template;
import freemarker.template.TemplateException;

import javax.inject.Inject;
import javax.servlet.ServletException;
import javax.servlet.annotation.MultipartConfig;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.Part;
import java.io.IOException;
import java.io.InputStream;
import java.io.PrintWriter;
import java.util.HashMap;
import java.util.Map;

@WebServlet("admin/upload-file")
@MultipartConfig
public class UploadFileServlet extends HttpServlet {

    private static final String SUCCESS_MESSAGE = "Plik został załadowany";

    private static final String FAILURE_MESSAGE = " Plik nie został załadowany.";

    @Inject
    TemplateProvider templateProvider;

    @Inject
    UploadService uploadService;

    @Override
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException {
        String message;
        boolean isPrintForm = false;
        try {
            Part filePart = req.getPart("file");
            InputStream fileContent = filePart.getInputStream();
            uploadService.uploadFile(fileContent);
            message = SUCCESS_MESSAGE;
        } catch (IOException e) {
            message = FAILURE_MESSAGE + e.getMessage();
            e.printStackTrace();
            isPrintForm = true;
        }
        printPage(resp, message, isPrintForm);
    }

    private void printPage(HttpServletResponse resp, String message, boolean isPrintForm) {
        try {
            resp.setContentType("text/html;charset=UTF-8");
            PrintWriter writer = resp.getWriter();
            Template template = templateProvider.getTemplate(getServletContext(), templateProvider.UPLOAD_FILE_TEMPLATE);

            Map<String, Object> model = new HashMap<>();
            model.put("message", message);
            model.put("isPrintForm", isPrintForm);

            template.process(model, writer);
        } catch (TemplateException | IOException e) {
            e.printStackTrace();
        }
    }

    @Override
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        printPage(resp, "", true);
    }
}
