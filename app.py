import SwiftUI
import PencilKit
import Combine

// MARK: - Model

struct User: Identifiable, Codable {
    var id = UUID()
    var nickname: String
    var username: String
    var password: String
}

struct Project: Identifiable, Codable {
    var id = UUID()
    var name: String
    var isShared: Bool
    var drawingData: Data
}

// MARK: - ViewModel

class AppViewModel: ObservableObject {
    @Published var currentUser: User?
    @Published var projects: [Project] = []
    @Published var sharedProjects: [Project] = []
    
    // Create a new project
    func createProject(name: String, isShared: Bool, drawingData: Data) {
        let project = Project(name: name, isShared: isShared, drawingData: drawingData)
        projects.append(project)
        if isShared { sharedProjects.append(project) }
    }
}

// MARK: - Views

struct LoginView: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var nickname = ""
    @State private var username = ""
    @State private var password = ""
    @State private var isLoggedIn = false
    
    var body: some View {
        if isLoggedIn {
            ProjectListView(viewModel: viewModel)
        } else {
            VStack(spacing: 20) {
                Text("Добро пожаловать!")
                    .font(.largeTitle)
                    .bold()
                TextField("Ник", text: $nickname)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                TextField("Username", text: $username)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                SecureField("Пароль", text: $password)
                    .textFieldStyle(RoundedBorderTextFieldStyle())
                
                Button(action: {
                    let user = User(nickname: nickname, username: username, password: password)
                    viewModel.currentUser = user
                    isLoggedIn = true
                }) {
                    Text("Войти")
                        .frame(maxWidth: .infinity)
                        .padding()
                        .background(Color.blue.opacity(0.8))
                        .foregroundColor(.white)
                        .cornerRadius(12)
                }
            }
            .padding()
        }
    }
}

struct ProjectListView: View {
    @ObservedObject var viewModel: AppViewModel
    @State private var newProjectName = ""
    @State private var showingDrawing = false
    @State private var selectedProject: Project?
    
    var body: some View {
        NavigationView {
            VStack {
                List {
                    Section(header: Text("Мои проекты")) {
                        ForEach(viewModel.projects) { project in
                            Button(action: {
                                selectedProject = project
                                showingDrawing = true
                            }) {
                                Text(project.name)
                                    .foregroundColor(.primary)
                                    .padding(6)
                            }
                        }
                    }
                    
                    Section(header: Text("Совместные проекты")) {
                        ForEach(viewModel.sharedProjects) { project in
                            Button(action: {
                                selectedProject = project
                                showingDrawing = true
                            }) {
                                Text(project.name + " 🔗")
                                    .foregroundColor(.purple)
                                    .padding(6)
                            }
                        }
                    }
                }
                
                HStack {
                    TextField("Название нового проекта", text: $newProjectName)
                        .textFieldStyle(RoundedBorderTextFieldStyle())
                    Button("Создать") {
                        // Создаём пустой проект с PKDrawing
                        let drawing = PKDrawing()
                        if let data = try? drawing.dataRepresentation() {
                            viewModel.createProject(name: newProjectName, isShared: false, drawingData: data)
                            newProjectName = ""
                        }
                    }
                    .padding(.horizontal, 10)
                    .background(Color.green.opacity(0.7))
                    .foregroundColor(.white)
                    .cornerRadius(8)
                }
                .padding()
                
                Button("Поделиться ссылкой для совместного проекта") {
                    // Здесь можно генерировать код/ссылку и отмечать проект как совместный
                    if let lastProject = viewModel.projects.last {
                        var sharedProject = lastProject
                        sharedProject.isShared = true
                        viewModel.sharedProjects.append(sharedProject)
                    }
                }
                .padding()
                .background(Color.orange.opacity(0.8))
                .foregroundColor(.white)
                .cornerRadius(12)
                .padding(.bottom)
            }
            .navigationTitle("Проекты")
            .sheet(isPresented: $showingDrawing) {
                if let project = selectedProject {
                    DrawingCanvasView(project: project)
                }
            }
        }
    }
}

struct DrawingCanvasView: View {
    @State var canvasView = PKCanvasView()
    var project: Project
    
    var body: some View {
        VStack {
            CanvasToolBar(canvasView: canvasView)
            CanvasViewWrapper(canvasView: canvasView)
        }
        .onAppear {
            if let drawing = try? PKDrawing(data: project.drawingData) {
                canvasView.drawing = drawing
            }
        }
    }
}

// MARK: - Canvas Toolbar

struct CanvasToolBar: View {
    var canvasView: PKCanvasView
    @State private var selectedTool: PKInkingTool.InkType = .pen
    @State private var color: Color = .black
    @State private var width: CGFloat = 5
    
    var body: some View {
        HStack(spacing: 15) {
            Picker("Инструмент", selection: $selectedTool) {
                Text("Карандаш").tag(PKInkingTool.InkType.pen)
                Text("Маркер").tag(PKInkingTool.InkType.marker)
                Text("Фломастер").tag(PKInkingTool.InkType.highlighter)
            }
            .pickerStyle(MenuPickerStyle())
            
            ColorPicker("", selection: $color)
                .frame(width: 50)
            
            Slider(value: $width, in: 1...20) {
                Text("Толщина")
            }
            
            Button("Ластик") {
                canvasView.tool = PKEraserTool(.bitmap)
            }
            
            Button("Очистить") {
                canvasView.drawing = PKDrawing()
            }
        }
        .padding()
        .onChange(of: selectedTool) { newValue in
            let tool = PKInkingTool(newValue, color: UIColor(color), width: width)
            canvasView.tool = tool
        }
        .onChange(of: color) { _ in
            let tool = PKInkingTool(selectedTool, color: UIColor(color), width: width)
            canvasView.tool = tool
        }
        .onChange(of: width) { _ in
            let tool = PKInkingTool(selectedTool, color: UIColor(color), width: width)
            canvasView.tool = tool
        }
    }
}

// MARK: - Canvas View Wrapper

struct CanvasViewWrapper: UIViewRepresentable {
    var canvasView: PKCanvasView
    
    func makeUIView(context: Context) -> PKCanvasView {
        canvasView.backgroundColor = UIColor.systemGray6
        canvasView.alwaysBounceVertical = true
        canvasView.drawingPolicy = .anyInput
        return canvasView
    }
    
    func updateUIView(_ uiView: PKCanvasView, context: Context) {}
}

// MARK: - App Entry

@main
struct SharedArtApp: App {
    @StateObject var viewModel = AppViewModel()
    
    var body: some Scene {
        WindowGroup {
            LoginView(viewModel: viewModel)
        }
    }
}
