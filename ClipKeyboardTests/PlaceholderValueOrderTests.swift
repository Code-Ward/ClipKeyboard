//
//  PlaceholderValueOrderTests.swift
//  ClipKeyboardTests
//
//  **빈칸 값의 순서**를 지킨다.
//
//  사용자 신고 그대로다.
//    "편집할 때마다 관리 빈칸 섹션이 자주 뒤집혀 있습니다."
//    "종종 {} 부분이 잘못되고, 배열 순서가 자주 뒤틀려집니다."
//
//  원인은 하나였다. 저장할 때 값마다 `addPlaceholderValue` 를 되풀이해 불렀는데,
//  그 함수는 하나씩 **맨 앞에** 꽂는다. 그래서 적어 둔 순서가 저장할 때마다 통째로
//  뒤집혔다. 다시 열면 뒤집힌 채로 보이고, 고쳐 저장하면 또 뒤집힌다.
//
//  ⚠️ 보이는 것만의 문제가 아니다. 키보드는 목록의 **첫 값**을 기본값으로 넣는다.
//     뒤집히면 맨 처음 적어 둔 값 대신 맨 나중 값이 들어간다.
//

import Testing
import Foundation
@testable import ClipKeyboard

@Suite("빈칸 값, 적어 둔 순서를 지킨다")
struct PlaceholderValueOrderTests {

    private func clean(_ token: String) {
        AppGroup.defaults?.removeObject(forKey: "placeholder_values_\(token)")
    }

    @Test("목록을 통째로 넣으면 적어 둔 순서 그대로다")
    func mergeKeepsOrder() {
        let token = "{이름-order-1}"
        clean(token); defer { clean(token) }

        MemoStore.shared.mergePlaceholderValues(["유미", "주디", "리이오"],
                                                for: token,
                                                sourceMemoId: UUID(),
                                                sourceMemoTitle: "인사")

        let got = MemoStore.shared.loadPlaceholderValues(for: token).map(\.value)
        #expect(got == ["유미", "주디", "리이오"], "뒤집히면 키보드가 넣는 기본값도 바뀐다")
    }

    @Test("두 번 저장해도 뒤집히지 않는다")
    func mergeIsStableAcrossSaves() {
        let token = "{이름-order-2}"
        clean(token); defer { clean(token) }
        let id = UUID()

        for _ in 0..<3 {
            MemoStore.shared.mergePlaceholderValues(["하나", "둘", "셋"],
                                                    for: token, sourceMemoId: id, sourceMemoTitle: "반복")
        }

        let got = MemoStore.shared.loadPlaceholderValues(for: token).map(\.value)
        #expect(got == ["하나", "둘", "셋"], "고쳐 저장할 때마다 순서가 달라지면 안 된다")
    }

    @Test("다른 데서 온 값은 뒤에 남는다")
    func mergeKeepsOthersBehind() {
        let token = "{이름-order-3}"
        clean(token); defer { clean(token) }

        MemoStore.shared.addPlaceholderValue("남의값", for: token,
                                             sourceMemoId: UUID(), sourceMemoTitle: "다른 단축어")
        MemoStore.shared.mergePlaceholderValues(["내값1", "내값2"],
                                                for: token, sourceMemoId: UUID(), sourceMemoTitle: "내 단축어")

        let got = MemoStore.shared.loadPlaceholderValues(for: token).map(\.value)
        #expect(got == ["내값1", "내값2", "남의값"])
    }

    @Test("빈 값과 공백은 걸러진다")
    func mergeDropsEmpties() {
        let token = "{이름-order-4}"
        clean(token); defer { clean(token) }

        MemoStore.shared.mergePlaceholderValues(["  유미 ", "", "   ", "주디"],
                                                for: token, sourceMemoId: UUID(), sourceMemoTitle: "정리")

        #expect(MemoStore.shared.loadPlaceholderValues(for: token).map(\.value) == ["유미", "주디"])
    }

    /// 값 **하나**를 올릴 때는 맨 앞이 맞다. 최근에 쓴 것이 앞에 오는 목록이다.
    @Test("하나를 올리면 맨 앞으로 온다")
    func addStillPromotesToFront() {
        let token = "{이름-order-5}"
        clean(token); defer { clean(token) }

        MemoStore.shared.mergePlaceholderValues(["하나", "둘"],
                                                for: token, sourceMemoId: UUID(), sourceMemoTitle: "처음")
        MemoStore.shared.addPlaceholderValue("둘", for: token,
                                             sourceMemoId: UUID(), sourceMemoTitle: "방금 씀")

        #expect(MemoStore.shared.loadPlaceholderValues(for: token).map(\.value) == ["둘", "하나"])
    }
}
